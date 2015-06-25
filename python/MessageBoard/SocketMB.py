
from MessageBoard import *
import SocketServer
import socket, select

USE_NODELAY = 1

###########################################################################
"""

  Here is the Client Base implementation.
  
"""
class SocketMessageClient(PeerMessageClient):
	def __init__(self, host=None, port=MESSAGE_BOARD_PORT, initPath="", marshaller=None):
		PeerMessageClient.__init__(self)
		if marshaller == None:
			marshaller = Marshaller()
		self.marshaller = marshaller
		if initPath == "" and os.path.exists(DEFAULT_INIT_FILE_PATH):
			initPath = DEFAULT_INIT_FILE_PATH
		dict = {}
		self.raiseExceptions = 0
		if initPath:
			dict = readParamFile(initPath)
		if dict.has_key("verbosity"):
			global verbosity
			verbosity = int(dict['verbosity'])
		if dict.has_key("RaiseExceptions"):
			self.raiseExceptions = string.atoi(dict['RaiseExceptions'])
		if host == None and dict.has_key("MessageBoardServerHost"):
			host = dict["MessageBoardServerHost"]
		if host == None:
			host = DEFAULT_MESSAGE_BOARD_HOST
		self.host = host
		self.port = port
		self.clientsock = None
		self.connected = 0
		self.connectToServer()
		if self.clientsock == None:
			print "Cannot connect to %s:%d" % (host, port)
		self.running = 1
		self.startReaderThread()

	def startReaderThread(self):
		if verbosity:
			print "Creating listener thread..."
			sys.stdout.flush()
		self.readerThread = threading.Thread(target = self.listener, args=(self,))
		self.readerThread.setDaemon(1)
		self.readerThread.isReaderThread = True
		self.readerThread.client = self
		self.readerThread.start()

	def isConnected(self):
		return self.connected != 0

	def connectToServer(self):
		if verbosity:
			print "Attempting to connect to %s:%d..." % (self.host, self.port)
		self.clientsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.clientsock.connect((self.host, self.port))
			self.connected = 1
			if verbosity:
				print "connected"
				print "Sending meta information"
			self.sendMetaInfo()
		except:
			self.clientsock = None
			self.connected = 0

	def listener(self, *args):
		if verbosity:
			print "listener running..."
			sys.stdout.flush()
		while self.running:
			while self.running and self.clientsock == None:
				self.connectToServer()
			try:
				self.readMessages()
			except NoServerException:
				pass
			try:
				if not threading.currentThread().isReaderThread:
					break
			except:
				print "Application exited without shutting down MB"
				return
			time.sleep(1)
		if verbosity:
			print "listener exiting..."

	def readMessages(self):
		self.buf = ''
		while self.running:
			try:
				str = self.clientsock.recv(1024)
				if verbosity > 1:
					print 'Received: """%s"""' % str
				if str == '':
					break
			except:
				print "Socket error"
				break
			self.buf = self.buf + str
			#	    while 1:
			while self.running:
				try:
					idx = string.index(self.buf, '\n}\n')
				except AttributeError:
					print "Application exited without shutting down MB"
					return
				except ValueError:
					break
				msgbuf = self.buf[:idx+3]
				self.buf = self.buf[idx+3:]
				try:
					msg = self.marshaller.unmarshal(msgbuf)
					self.handleMessage(msg)
					if not threading.currentThread().isReaderThread:
						return
				except:
					print "Bad Message Buf:", msgbuf
		self.noticeServerClosed()

	def noticeServerClosed(self):
		self.clientsock = None
		self.connected = 0
		print "Socket closed"
		raise NoServerException

	def sendString(self, str):
		if verbosity > 1:
			print 'Sending: """%s"""' % str
			sys.stdout.flush()
		if not self.isConnected():
			raise NoServerException
		try:
			self.clientsock.send(str)
		except:
			traceback.print_exc(file=sys.stderr)
			self.noticeServerClosed()

	def setMarshallerType(self, marshallerType):
		if marshallerType == "JSON":
			import JSONMarshaller
			jsonMarshaller = JSONMarshaller.JSONMarshaller(verbosity)
			print "marshaller", jsonMarshaller
			self.marshaller = jsonMarshaller
		self.sendCommandLine("marshaller "+marshallerType)

	def sendCommandLine(self, str):
		self.sendString(str+"\n\n")

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
			self.clientsock.shutdown(1)
		except:
			print "SocketMB.Client %s error on finish" % self.host
			traceback.print_exc(file=sys.stderr)

	def shutdown(self):
		self.running = 0
		print "self.running =", self.running
		self.finish()


#########################################################################################
"""

  Here are the Server Side classes.

  The SocketMessageServer listens for new clients.  When a new client
  appears, it spawns a SocketPeerHandler to communicate with that client.
  Actual messages are handled by a MessageHandler.

  In a pure blackboard configuration, the message server does no processing of
  commands, and only propagates them to other clients.  If MessageBoard.py is
  run directly from the command line, that will be the configuration.

  However, in some cases the blackboard server will be combined with
  an implementation for handling some of the messages.  That can improve
  performance slightly, and also require one less running program.  And
  in some cases, a server may want to use this message framework not for
  blackboard purposes, but just to handle simple unshared requests from
  clients.  In those cases, it is usually sufficent to simply override
  the MessageHandler class to implement the desired behavior.

  
"""
class SocketPeerHandler(SocketServer.BaseRequestHandler, PeerHandler):
	def __init__(self, request, client_address, server):
		host, port = client_address
		hostname = socket.getfqdn(host)
		self.marshaller = Marshaller()
		clientAddress = "%s %s" % (hostname, `client_address`)
		self.numDropped = 0
		self.nonBlocking = 1
		self.haveSetNonblocking = 0
		PeerHandler.__init__(self, "Socket", server.hub, clientAddress)
		self.setSockOpts(request)
		SocketServer.BaseRequestHandler.__init__(self,
												 request,
												 client_address,
												 server)

	def setSockOpts(self, sock):
		if not USE_NODELAY:
			return
		print "Getting TCP_NODELAY"
		opt = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY)
		print "TCP_NODELAY = ", opt
		print "Setting TCP_NODELAY"
		sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		opt = sock.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY)
		print "TCP_NODELAY = ", opt

	def handleMessage(self, msgbuf):
		self.numReceived += 1
		msg = None
		try:
			msg = self.marshaller.unmarshal(msgbuf)
		except ValueError:
			print "Bad message buffer:", msgbuf
			self.numBadReceived += 1
			return
		self.lastReceived = msg
		self.server.hub.handleMessage(self, msg, msgbuf, self.marshaller.type)

	def sendMessage(self, msg, msgbuf, marshallType):
		if msgbuf == None or marshallType != self.marshaller.type:
			msgbuf = self.marshaller.marshal(msg)
		if verbosity > 1:
			print "Sending: '''%s'''\n" % msgbuf
		if self.nonBlocking:
			self.sendMessageNonBlocking(msg, msgbuf)
		else:
			self.sendMessageBlocking(msg, msgbuf)
		self.numSent += 1
		self.lastSent = msg

	def sendMessageBlocking(self, msg, msgbuf):
		#	self.request.send(msgbuf+"\n")
		self.request.sendall(msgbuf+"\n")

	def sendMessageNonBlocking(self, msg, msgbuf):
		if not self.haveSetNonblocking:
			self.haveSetNonblocking = 1
			print "Setblocking(0)...",
			try:
				self.request.setblocking(0)
			except:
				print "Failed to setblocking(0)"
				print "request:", self.request
				traceback.print_exc(file=sys.stderr)
			print "ok"
		try:
			n = self.request.send(msgbuf+"\n")
			if n < len(msgbuf)+1:
				print "Overflow"
		except socket.error:
			self.numDropped += 1
			if self.numDropped == 1:
				e,v,tb = sys.exc_info()
				print "First Overflow detected"
				print "Exception:", e
				print "Value:", v
				print "request:", self.request
				traceback.print_exc(file=sys.stderr)
			if self.numDropped % 1000 == 0:
				print "Num Overflows", self.numDropped
		except:
			e,v,tb = sys.exc_info()
			print "First Overflow detected"
			print "Exception:", e
			print "Value:", v
			traceback.print_exc(file=sys.stderr)

	def readBytes(self, size):
		if self.nonBlocking:
			select.select([self.request], [], [])
		return self.request.recv(size)

	#
	# Not used.  Bad alternative to using select...
	#
	def readBytesByPolling(self, size):
		while 1:
			try:
				return self.request.recv(size)
			except:
				traceback.print_exc(file=sys.stderr)
				print "Will wait for a while..."
				time.sleep(1)

	def handleCommandLine(self, buf):
		print "****** commandLine: '%s'" % buf
		parts = buf.split()
		if len(parts) == 2 and parts[0] == "marshaller":
			marshallerType = parts[1]
			print "--->>", marshallerType
			if marshallerType == "JSON":
				import JSONMarshaller
				jsonMarshaller = JSONMarshaller.JSONMarshaller(1)
				print "marshaller", jsonMarshaller
				self.marshaller = jsonMarshaller

	def handle(self):
		print "New client..."
		hub = self.server.hub
		print self.getInfo()
		hub.registerPeerHandler(self)
		hub.showInfo(sys.stdout)
		self.running = 1
		self.buf = ''
		while self.running:
			try:
				str = self.readBytes(1024)
				if verbosity > 1:
					print 'Received: """%s"""' % str
			except:
				traceback.print_exc(file=sys.stderr)
				self.wrapup()
				self.running = 0
				break
			if str == '':
				print "Request completed"
				self.wrapup()
				self.running = 0
				sys.stdout.flush()
				break
			self.buf = self.buf + str
			while 1:
				idx1 = self.buf.find('\n\n')
				idx2 = self.buf.find('\n}\n')
				if idx1 >= 0 and (idx2 < 0 or idx1 < idx2):
					msgbuf = self.buf[:idx1]
					self.buf = self.buf[idx1+2:]
					self.handleCommandLine(msgbuf)
					continue
				if idx2 < 0:
					break
				msgbuf = self.buf[:idx2+3]
				self.buf = self.buf[idx2+3:]
				self.handleMessage(msgbuf)


class SocketMessageServer(SocketServer.ThreadingTCPServer, Gateway):
	def __init__(self, hub, server_address=None,
				 messageHandlerFactory=SimpleMessageHandler,
				 SocketHandlerClass=SocketPeerHandler):
		if server_address == None:
			server_address = ('',MESSAGE_BOARD_PORT)
		self.messageHandlerFactory = messageHandlerFactory
		self.hub = hub
		SocketServer.ThreadingTCPServer.allow_reuse_address
		print "****** Setting allow_reuse_address True *******"
		SocketServer.ThreadingTCPServer.allow_reuse_address = True
		SocketServer.ThreadingTCPServer.__init__(self, server_address, SocketHandlerClass)

	def serve_forever(self):
		self.handlers = []
		self.running = 1
		while self.running:
			self.handle_request()


def runSocketServer_(server, messageHandlerFactory):
	sa = server.socket.getsockname()
	print "Running TCP    gateway on port", sa[1]
	sys.stdout.flush()
	server.serve_forever()

def runSocketServer(server=None, useThread=0, messageHandlerFactory=SimpleMessageHandler, hub=None):
	if server == None:
		server = SocketMessageServer(hub, messageHandlerFactory=messageHandlerFactory)
		server.hub = hub
	if useThread:
		thread = threading.Thread(target=runSocketServer_, args=(server, messageHandlerFactory))
		thread.setDaemon(1)
		server.thread = thread
		thread.start()
		return server
	else:
		runSocketServer_()


