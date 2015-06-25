
from MessageBoard import *
import SocketServer
import sys, socket, traceback

verbosity = 1

MCAST_MESSAGE_BOARD_ADDRESS = "235.0.50.5"
MCAST_MESSAGE_BOARD_PORT = 54321
MCAST_LOOPBACK = 0

###########################################################################
"""

  Here is the Client Base implementation.
  
"""
class MCastMessageClient(PeerMessageClient):
    def __init__(self, addr=None, port=None, initPath="", marshaller=None):
	PeerMessageClient.__init__(self)
	if addr == None:
	    addr = MCAST_MESSAGE_BOARD_ADDRESS
	if port == None:
	    port = MCAST_MESSAGE_BOARD_PORT
        if marshaller == None:
            marshaller = Marshaller()
        self.marshaller = marshaller
	if initPath == "" and os.path.exists(DEFAULT_INIT_FILE_PATH):
	    initPath = DEFAULT_INIT_FILE_PATH
	dict = {}
	self.raiseExceptions = 0
	if initPath:
	    dict = readParamFile(initPath)
	if dict.has_key("Verbosity"):
	    global verbosity
	    verbosity = string.atoi(dict['Verbosity'])
	if dict.has_key("RaiseExceptions"):
	    self.raiseExceptions = string.atoi(dict['RaiseExceptions'])
	self.msgIdx = 0
	self.port = port
	self.addr = addr
	self.insocket = None
	self.outsocket = None
	self.connectToServer()
	if self.insocket == None:
	    print "Cannot get mcast socket for port %d" % port
        print "Creating listener thread..."
	sys.stdout.flush()
	self.running = 1
        self.thread = threading.Thread(target = self.listener, args=(self,))
	self.thread.setDaemon(1)
	self.thread.start()

    def isConnected(self):
	return self.insocket != None and self.outsocket != None

    def connectToServer(self):
        print "Attempting to connect to %s:%d..." % (self.addr, self.port)
	try:
	    print "Getting input socket"
            self.insocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM , socket.IPPROTO_UDP)
	    #self.insocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	    self.insocket.bind((self.addr, self.port))
	    self.insocket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
            self.insocket.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP,
	    		socket.inet_aton(self.addr) + socket.inet_aton(("0.0.0.0")))
	    self.insocket.setblocking(0)
            #import struct
            #mreq = struct.pack("4sl", socket.inet_aton(self.addr), socket.INADDR_ANY)
	    #self.insocket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
	    #self.insocket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, MCAST_LOOPBACK)
            print "connected"
	    print "Sending meta information"
	    #self.sendMetaInfo()
	except:
	    print "Error getting input socket"
            traceback.print_exc(file=sys.stderr)
            self.insocket = None
	    return
	try:
	    print "Getting output socket"
            #self.outsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
   	    #self.outsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	    #self.outsocket.connect((self.addr, self.port))
	    #self.outsocket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_TTL, 2)
	    #self.outsocket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 1)
	except:
	    print "Error getting output socket"
            traceback.print_exc(file=sys.stderr)
            self.outsocket = None

    def listener(self, *args):
        print "listener running..."
	sys.stdout.flush()
	while self.running:
	   while self.running and self.insocket == None:
	      self.connectToServer()
	   try:
	      self.readMessages()
	   except NoServerException:
	      pass
	   time.sleep(1)
        print "listener exiting..."

    def readMessages(self):
	print "Hello"
        while self.running:
            try:
                msgbuf, sender = self.insocket.recvfrom(4096)
	        if verbosity > 1:
	            print "Received: ", msgbuf
	        if msgbuf == '':
	            break
	        idx = string.index(msgbuf, '\n')
	        headerLine = msgbuf[:idx]
	        if verbosity > 1:
	           print "Sender:", sender
	           print "Header:", headerLine
	        msgbuf = msgbuf[idx+1:]
	    except:
		print "*** Error getting message ***"
                traceback.print_exc(file=sys.stderr)
	        break
            try:
	        msg = self.marshaller.unmarshal(msgbuf)
	    except:
	        print "Cannot unmarshal", msgbug
	        return
            for messageHandler in self.messageHandlers:
	        try:
                    messageHandler.handleMessage(msg)
	        except:
                    traceback.print_exc(file=sys.stderr)
	            print "* Error in handler"
        self.noticeServerClosed()

    def noticeServerClosed(self):
	self.insocket = None
	print "Socket closed"
	raise NoServerException

    def genMsgIdx(self):
	self.msgIdx += 1
	return self.msgIdx

    def sendString(self, str):
	""" For now we don't send a header.  But we reserve the	
	first line for possible future header that might describe
	marshalling type, sequence number to help with large
	multipacket messages, etc."""
	msgIdx = self.genMsgIdx()
	headerLine = "MBMP 0.0 %s %s 1 1\n" % (self.clientName, msgIdx)
	str = headerLine + str
	if not self.isConnected():
	    raise NoServerException
	try:
            if verbosity > 1:
                print "Sending:", str
                sys.stdout.flush()
            self.outsocket.send(str, 0)
	except:
            traceback.print_exc(file=sys.stderr)
	    self.noticeServerClosed()

    def sendMetaInfo(self):
	pass

    def sendMessage(self, dict):
        str = self.marshaller.marshal(dict)
	if self.raiseExceptions:
	    self.sendString(str)
	else:
	    if not self.isConnected():
	        print "No server"
		return -1
	    try:
	        self.sendString(str)
	        return 0
	    except:
		print "dropped message"
                traceback.print_exc(file=sys.stderr)
	        return -1

    def finish(self):
	try:
           self.insocket.shutdown(1)
           self.outsocket.shutdown(1)
        except:
	   print "MCastMessageClient.py %s error on finish" % self.port
           traceback.print_exc(file=sys.stderr)

    def shutdown(self):
	self.running = 0
	print "self.running =", self.running
	self.finish()


