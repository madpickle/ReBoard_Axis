
from MessageBoard import *
from HTTPMB import *
import urllib, urllib2, traceback

#
# This should use the HTTPMB URLMarshaller, but I think some things
# need to be fixed or checked in that...
#
def urlEncode(dict):
    s = ""
    for key in dict.keys():
        kstr = urllib.quote(key)
        vstr = urllib.quote("%s" % str(dict[key]))
	s += "%s=%s&" % (kstr, vstr)
    return s[:-1]

class HTTPMessageClient(PeerMessageClient):
#class HTTPMessageClient(BaseMessageClient):
    def __init__(self, host=None, port=MESSAGE_BOARD_HTTP_PORT, initPath="", marshaller=None):
	PeerMessageClient.__init__(self)
	#BaseMessageClient.__init__(self)
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
	if host == None and dict.has_key("MessageBoardServerHost"):
	    host = dict["MessageBoardServerHost"]
        if host == None:
            host = DEFAULT_MESSAGE_BOARD_HOST
	self.host = host
	self.port = port
	self.httpStream = None
	self.connected = 0
	self.connectToServer()
	if self.httpStream == None:
	    print "Cannot connect to %s:%d" % (host, port)
        print "Creating listener thread..."
	sys.stdout.flush()
	self.running = 1
        self.thread = threading.Thread(target = self.listener, args=(self,))
	self.thread.setDaemon(1)
	self.thread.start()

    def isConnected(self):
	return self.connected != 0

    def connectToServer(self):
        print "Attempting to connect to %s:%d..." % (self.host, self.port)
	try:
	    connectionUrl = "http://%s:%d/watchMessages" % (self.host, self.port)
	    print "Opening", connectionUrl
            self.httpStream = urllib2.urlopen(connectionUrl)
	    print "Got httpStream", self.httpStream
	    self.httpStream.readline()
	    self.httpStream.readline()
	    self.connected = 1
            print "connected"
	except:
            traceback.print_exc(file=sys.stderr)
            self.httpStream = None
	    self.connected = 0

    def listener(self, *args):
        print "listener running..."
	sys.stdout.flush()
	while self.running:
	   while self.running and self.httpStream == None:
	      self.connectToServer()
	   try:
	      self.readMessages()
	   except NoServerException:
	      pass
	   time.sleep(1)
        print "listener exiting..."

    def readMessages(self):
	self.buf = ''
        while self.running:
            try:
                str = self.httpStream.readline()
	        if str == '':
	            break
	    except:
		print "HTTP Connectiont error"
	        break
	    self.buf = self.buf + str
	    while 1:
	        try:
                   idx = string.index(self.buf, '\n}\n')
	        except ValueError:
	           break
	        msgbuf = self.buf[:idx+3]
	        self.buf = self.buf[idx+3:]
		msg = self.marshaller.unmarshal(msgbuf)
	        for messageHandler in self.messageHandlers:
                     messageHandler.handleMessage(msg)
        self.noticeServerClosed()

    def noticeServerClosed(self):
	self.httpStream = None
	self.connected = 0
	print "HTTP Connection closed"
	raise NoServerException

    def sendMetaInfo(self):
	print "We don't send meta info"

    def sendMessage(self, dict):
	str = urlEncode(dict)
	url = "http://%s:%d/sendMessage?%s" % (self.host, self.port, str)
	print url
	try:
   	    uos = urllib2.urlopen(url)
	    uos.close()
	except:
	    print "Couldn't send message"

    def finish(self):
	try:
	   if self.httpStream:
               self.httpStream.close()
        except:
	   print "HTTPMB.Client %s error on finish" % self.host
           traceback.print_exc(file=sys.stderr)

    def shutdown(self):
	self.running = 0
	print "self.running =", self.running
	self.finish()


def test():
    class Handler(SimpleMessageHandler):
	def handleMessage(self, msg):
	    print msg

    hostname = "localhost"
    handler = Handler()
    client = HTTPMessageClient(hostname)
    client.registerMessageHandler(handler)
    client.sendMessage({'msgType':'test', 'value':'hello', 'num':25})
    client.listenForever()

def testMarshal(dict):
    print "dict:", dict
    print "urlEncode:", urlEncode(dict)
    m = URLMarshaller()
    str = m.marshal(dict)
    print "Str:", str
    dict = m.unmarshal(str)
    print "dict:", dict
    print


def test0():
    testMarshal(  {'str':"Hello world", 'num':25}  )

if __name__ == '__main__':
    test()

