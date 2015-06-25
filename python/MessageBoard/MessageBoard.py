
import sys, string, time, urllib, traceback
import socket
import types
import os, os.path
import threading
import Queue
import StringIO
import cStringIO
import copy
import MessageFile
import random

__version__ = "0.3"

verbosity = 0

PARANOID = 0
MCAST_GATEWAY = 0

DEFAULT_MESSAGE_BOARD_HOST = "localhost"
MESSAGE_BOARD_PORT = 8500
MESSAGE_BOARD_HTTP_PORT = 8010
MESSAGE_BOARD_XMLRPC_PORT = 9500

MBRPC_TIMEOUT = 2
SUBSCRIPTION_TIMEOUT = 30

env = os.environ
try:
	DOTSDIR = env['DOTSDIR']
except KeyError:
	DOTSDIR = "D:/DOTS"
try:
	DEFAULT_INIT_FILE_PATH = env['MB_INIT_FILE_PATH']
except KeyError:
	DEFAULT_INIT_FILE_PATH = os.path.join(DOTSDIR, "MessageBoard/MessageBoard.init")
	DEFAULT_INIT_FILE_PATH = DEFAULT_INIT_FILE_PATH.replace("\\","/")

#NoServerException = "NoServerException"
class NoServerException(Exception):
	pass

LAST_REQUEST_ID = None

def getRequestId():
	# Should change this to a string that is more unique
	global LAST_REQUEST_ID
	if LAST_REQUEST_ID == None:
		LAST_REQUEST_ID = int(10000000*random.random())
	LAST_REQUEST_ID += 1
	return LAST_REQUEST_ID

def defaultClientName():
	baseName = os.path.basename(sys.argv[0])
	return "%s_%s_%d" % (baseName, socket.gethostname(), os.getpid())

#
# Some helper functions for getting a typed value from dict
#
def getInt(dict, key):
	val = dict[key]
	if type(val) == type("String"):
		val = string.atoi(val)
	return val

def getFloat(dict, key):
	val = dict[key]
	if type(val) == type("String"):
		val = string.atof(val)
	return val

class Counter:
	def __init__(self):
		self.dict = {}

	def count(self, key):
		if self.dict.has_key(key):
			self.dict[key] += 1
		else:
			self.dict[key] = 1

	def keys(self):
		keys = self.dict.keys()
		keys.sort()
		return keys

	def __setitem__(self, key, val):
		self.dict[key] = val

	def __getitem__(self, key):
		return self.dict[key]

MINS = 60
HOURS = 60*MINS
DAYS = 24*HOURS

def durString(t):
	if t > DAYS:
		return "%.1f days" % (t / DAYS)
	if t > HOURS:
		return "%.1f hours" % (t / HOURS)
	if t > MINS:
		return "%.1f mins" % (t / MINS)
	return "%.1f secs" % t


def itemMatches(pstr, tstr):
	if pstr == tstr:
		return 1
	if type(pstr) not in [type("str"), type(u"str")]:
		return 0
	if pstr[-1:] == "*":
		if pstr[:-1] == tstr[:len(pstr)-1]:
			return 1
	return 0

def dictMatches(pmsg, tmsg):
	#print "dictMatches: ", pmsg, tmsg
	if pmsg == None:
		return 1
	for key in pmsg.keys():
		if not tmsg.has_key(key):
			return 0
		if not itemMatches(pmsg[key], tmsg[key]):
			return 0
	return 1

"""
def check(s1, s2):
    print s1, s2, strMatches(s1, s2)

check("foo", "foo")
check("foo", "fo")
check("foo", "foob")
check("foo*", "foo")
check("foo*", "fo")
check("foo*", "foobar")
check("foo*", "foo.bar")
check("*", "")
check("*", "xxx")
sys.exit(1)
"""

class Pattern:
	def __init__(self, msgDict=None):
		if msgDict == None:
			self.pmsgs = []
		else:
			self.setDict(msgDict)

	def clear(self):
		self.pmsgs = []

	def addDict(self, msgDict):
		if msgDict == None:
			msgDict = {}
		self.pmsgs.append(msgDict)

	def setDict(self, msgDict):
		self.pmsgs = [msgDict]

	def matches(self, tmsg):
		#print "matches: ", self.pmsgs, tmsg
		for pmsg in self.pmsgs:
			if dictMatches(pmsg, tmsg):
				return 1
		return 0

	def __repr__(self):
		return `self.pmsgs`


class PythonMarshaller:
	type = "Python"

	def marshal(self, obj):
		#	return str(obj)
		dict = obj
		os = cStringIO.StringIO()
		os.write("{\n")
		for key in dict.keys():
			os.write("%s: %s,\n" % (`key`, `dict[key]`))
		os.write("}\n")
		os.seek(0)
		return os.read()

	def unmarshal(self, buf):
		try:
			obj = eval(buf)
		except:
			print "Bad message cannot unmarshal: ", buf
			raise ValueError
		return obj

class JavaScriptMarshaller:
	type = "JavaScript"
	def marshal(self, dict):
		str = '<script language="JavaScript">\n'
		str += "msg = new Object();\n"
		for key in dict.keys():
			str += "msg[%s] = %s;\n" % (`key`, `dict[key]`)
		str += "top.mb_noticeMessage(msg);\n"
		str += '</script><p>\n'
		return str

class XMLMarshaller:
	type = "XML"
	def marshal(self, dict):
		str = '  <message>\n'
		for key in dict.keys():
			str += "  <field>\n"
			str += "    <name>%s</name>\n" % key
			str += "    <value>%s</value>\n" % dict[key]
			str += "  </field>\n"
		str += '  </message>\n'
		return str

Marshaller = PythonMarshaller

def readParamFile(path):
	try:
		infile = open(path, 'r')
		print "Reading init file", path
	except:
		print "No init file"
		return None
	dict = {}
	for line in infile.readlines():
		line = string.strip(line)
		if line == "":
			continue
		if line[:1] == '#':
			continue
		try:
			idx = string.index(line, ":")
			key = line[:idx]
			val = string.strip(line[idx+1:])
			dict[key] = val
		except ValueError:
			print "Bad line %s in %s" % (`line`, path)
			print
			raise ValueError
	for key in dict.keys():
		dict[key.lower()] = dict[key]
	return dict



#
# Base class for message handler.  Normally this
# would be subclassed to provide a nontrivial
# implementation of handleMessage.
#
class SimpleMessageHandler:
	def __init__(self):
		self.pattern = Pattern()

	def handleMessage(self, msg):
		if verbosity:
			print msg

	def handleMessages(self, msgs):
		"""
        This is not normally defined in subclasses, but
        is provided in case in the future a batch of messages
        are provided, a handler can give them special treatment.
        """
		for msg in msgs:
			self.handleMessage(msg)


class LambdaMessageHandler(SimpleMessageHandler):
	def __init__(self, fun):
		SimpleMessageHandler.__init__(self)
		self.fun = fun

	def handleMessage(self, msg):
		self.fun(msg)

class DummyMessageHandler(SimpleMessageHandler):
	def handleMessage(self, msg):
		pass

class QueuedMessageHandler(SimpleMessageHandler):
	def __init__(self):
		SimpleMessageHandler.__init__(self)
		self.lock = threading.Lock()
		self.msgs = []

	def handleMessage(self, msg):
		self.lock.acquire()
		self.msgs.append(msg)
		self.lock.release()

	def getMessages(self):
		self.lock.acquire()
		msgs = self.msgs
		self.msgs = []
		self.lock.release()
		return msgs

##############################################################################
#
#  Server Side Base Classes
#

class ReportGenerator:
	def __init__(self, hub):
		self.hub = hub

	def genHandlerInfo(self, handler, ostr):
		ostr.write("%s Client: %s\n" % (handler.clientType, handler.clientAddress))
		et = time.time() - handler.joinTime
		prefix = " "
		str = prefix + "Started %s (%s)\n" % (time.ctime(handler.joinTime), durString(et))
		str += (prefix + "Messages sent to: %d (%d dropped)  received from: %d\n" % \
				(handler.numSent, handler.numDropped, handler.numReceived))
		str += (prefix + "Pattern: %s\n" % handler.pattern)
		ostr.write(str+"\n")


	def genReport(self, ofile=None):
		if ofile == None:
			ofile = sys.stdout
		hub = self.hub
		hostname = socket.gethostname()
		ofile.write("Status Report for MessageBoard on %s " % hostname)
		ofile.write("(Version %s)\n" % __version__)
		startTime = hub.startTime
		rt = time.time() - startTime
		ofile.write("Started %s (%d)\n" % (time.ctime(startTime), durString(rt)))
		ofile.write("Num Received: %d\n" % hub.numReceived)
		ofile.write("%d active clients:\n" % len(hub.peerHandlers))
		for handler in hub.peerHandlers:
			self.genHandlerInfo(handler, ofile)
		ofile.write("\nMessage Type Summary:\n")
		for key in hub.counter.keys():
			ofile.write("%8d %-25s\n" % (hub.counter[key], key))


class GatewayClientMessageHandler(SimpleMessageHandler):
	def __init__(self, client, hub):
		SimpleMessageHandler.__init__(self)
		self.gatewayClient = client
		self.hub = hub

	def handleMessage(self, msg):
		if verbosity > 1:
			print "***** Gateway client forwarding to hub"
		self.hub.handleMessage(self.gatewayClient, msg, None, None)


class MessageServerHub:
	"""
    A MessageBoard server process typically has several servers listening
    for messages coming via different transports or marshalling.  Each of
    those servers may get a connection from a client process and create
    a PeerHandler which receives messages from that client and can send
    messages to it.  The ServerHub keeps track of all such PeerHandlers.
    When it receives a message from any handler, it calls any message
    handlers that have been registered with the hub, and also propagates
    the message to all other handlers.

    A MessageClient may also be registered with the hub, and acts in the
    same way as a peer handler.  This may be used to connect MessageBoard
    servers together into a confederation.
    """
	def __init__(self, initPath=""):
		if initPath == "" and os.path.exists(DEFAULT_INIT_FILE_PATH):
			initPath = DEFAULT_INIT_FILE_PATH
		dict = {}
		if initPath:
			dict = readParamFile(initPath)
		if dict.has_key("verbosity"):
			global verbosity
			verbosity = int(dict['verbosity'])
		if verbosity > 0:
			print "****** Creating Server Hub"
		self.counter = Counter()
		self.lastMessageByType = {}
		self.lastTimeByType = {}
		self.lastPeerByType = {}
		self.numReceived = 0
		self.gatewayClients = []
		self.peerHandlers = []
		self.peerHandlerDict = {}
		self.messageHandlers = []
		self.messageCache = None
		self.startTime = time.time()
		self.reportGenerator = ReportGenerator(self)

	def registerMessageHandler(self, messageHandler, pattern=None):
		if type(pattern) == type("str"):
			pattern = {'msgType': pattern}
		messageHandler = getHandlerObject(messageHandler)
		messageHandler.pattern.addDict(pattern)
		self.messageHandlers.append(messageHandler)

	def unregisterMessageHandler(self, messageHandler):
		self.messageHandlers.remove(messageHandler)

	def registerPeerHandler(self, peerHandler, pattern=None):
		peerHandler.pattern = Pattern(pattern)
		self.peerHandlers.append(peerHandler)
		self.peerHandlerDict[peerHandler.peerName()] = peerHandler

	def unregisterPeerHandler(self, handler):
		try:
			self.peerHandlers.remove(handler)
		except:
			print "*** peerHandler already removed"
		try:
			del self.peerHandlerDict[handler.peerName()]
		except:
			print "*** peerHandler already removed"

	def registerGatewayClient(self, client, incomingPattern=None, outgoingPattern=None):
		print "Registering Gateway Client:", client.clientName
		client.outgoingPattern = outgoingPattern
		handler = GatewayClientMessageHandler(client, self)
		client.gateMessageHandler = handler
		self.gatewayClients.append(client)
		client.registerMessageHandler(handler, incomingPattern)

	def unregisterGatewayClient(self, client):
		self.gatewayClients.remove(client)

	def handleSystemMessage(self, peerHandler, msg):
		"""
        This gets called to manipulate patterns for a peerHandler.
        Normally it manipulates the same peer that it came in on,
        but if the system message contains "system.subscriptionId"
        field, it manipulates the peer handler for that instead.
        """
		sysMsgType = msg["system.msgType"]
		peerName = peerHandler.peerName()
		if msg.has_key("system.subscriptionId"):
			peerName = msg["system.subscriptionId"]
		if sysMsgType == 'subscribe':
			timeout = SUBSCRIPTION_TIMEOUT
			if msg.has_key("system.subscriptionTimeout"):
				timeout = getFloat(msg, "system.subscriptionTimeout")
			if not self.peerHandlerDict.has_key(peerName):
				sub = SubscriptionHandler("Subscription", self,
										  peerHandler.clientAddress,
										  peerName, timeout)
				if msg.has_key("system.clientDescription"):
					sub.clientDescription = msg["system.clientDescription"]
				self.registerPeerHandler(sub)
			return
		if sysMsgType == "clientDescription":
			peerHandler.clientDescription = msg["clientDescription"]
			return
		peerHandler = self.peerHandlerDict[peerName]
		msg = copy.copy(msg)
		for key in msg.keys():
			if key[:len("system.")] == "system.":
				print "pruning system field:", key
				del msg[key]
		if sysMsgType == "pattern.clear":
			peerHandler.pattern.clear()
			return
		if sysMsgType == "pattern.add":
			peerHandler.pattern.addDict(msg)
			return
		print "************************************"
		print "Unrecognized system Message:", msg

	def handleMessage(self, source, msg, buf, marshallType):
		"""
        This should be called by PeerHandlers or gatewayClients
            when they have received messages.  It will call any
            handlers registered with this hub and forward the
            message to all other handlers.

            source is the PeerHandler or gatewayClient

        """
		isPeerHandler = 0
		try:
			sourceName = source.peerName()
			isPeerHandler = 1
		except:
			try:
				sourceName = source.clientName
			except:
				print "**** Cannot get source Name for:", source
		#print "hub.handleMessage: ", peerHandler, buf, msg
		msgType = "undefined"
		if msg.has_key("msgType"):
			msgType = msg["msgType"]
		if msg.has_key("system.msgType"):
			if isPeerHandler:
				self.handleSystemMessage(source, msg)
			return
		self.counter.count(msgType)
		self.lastMessageByType[msgType] = msg
		self.lastTimeByType[msgType] = time.time()
		sourceName = "unknown"
		self.lastPeerByType[msgType] = sourceName
		for messageHandler in self.messageHandlers:
			if messageHandler.pattern:
				if not messageHandler.pattern.matches(msg):
					continue
			try:
				messageHandler.handleMessage(msg)
			except:
				traceback.print_exc()
		self.propagateMessage(source, msg, buf, marshallType)

	def sendMessages(self, msgs):
		for msg in msgs:
			self.sendMessage(msg)

	def sendMessage(self, msg):
		self.propagateMessage(None, msg, None, None)

	def propagateMessage(self, source, msg, msgbuf, marshallType):
		"""
            This sends a command to all listening clients.
            It currently runs in the calling thread which is
            bad, because it is throttled by the slowest client.
            It should put the command into a queue to be
            handled by another thread.

        source is the peerHandler or client that gave us this message.
        It will not be sent back to the source.
        """
		self.numReceived += 1
		op = None
		if msg and msg.has_key('msgType'):
			op = msg['msgType']
		deadPeerHandlers = []
		for h in self.peerHandlers:
			if h == source:
				continue
			if h.pattern != None and not h.pattern.matches(msg):
				continue
			try:
				h.sendMessage(msg, msgbuf, marshallType)
			except:
				print "---------------------------------"
				print "Failed to send to", h
				traceback.print_exc(file=sys.stderr)
				print "---------------------------------"
				deadPeerHandlers.append(h)

		for h in deadPeerHandlers:
			print "Removing handler", h
			try:
				self.unregisterPeerHandler(h)
			except ValueError:
				print "Already gone."

		for client in self.gatewayClients:
			if client == source:
				continue
			if client.outgoingPattern == None or \
					client.outgoingPatter.matches(msg):
				if verbosity > 1:
					print "***** Forwarding to gateway client"
				client.sendMessage(msg)


	def showInfo(self, ostr, detail=1):
		ostr.write("-------------\n")
		ostr.write("%d active clients:\n" % len(self.peerHandlers))
		for handler in self.peerHandlers:
			ostr.write("%s" % handler.getInfo())
			if detail:
				ostr.write(handler.getStats())

	def genReport(self, ofile=None):
		self.reportGenerator.genReport(ofile)

	def listenForever(self):
		self.running = 1
		while self.running:
			time.sleep(10)


"""
To extend MessageBoard to another type of transport and/or marshalling scheme,
it is simply necessary to subclass Gateway and PeerHander.
"""
class Gateway:
	pass

class PeerHandler:
	"""
    The main work in adding a new type of transport/marshalling gateway is
    defining a PeerHandler.  When a remote client connection is made to the
    gateway server, it typically will create a PeerHandler for that remote
    client.

    There are two main things the peer handler must do.  It must be able
    to receive marshalled posted messages from its peer, unmarshal them,
    and send them to the hub, which will cause them to be propagated to
    other peers, as appropriate.   It does this by calling

       hub.propateMessage(self, msg, msgbuf, marshallType)

    it passes the msgbuf and marshall type to the hub, simply for performance
    reasons, so that if the message is forwarded to other peers of the same
    type, it may not be necessary to remarshall it.

    The other thing the PeerHandler must do is send messages to its peer.
    It does this by implementing the method:

       sendMessage(self, msg, msgbuf, marshallType)

    It may mashall the message, or check that the msgbuf passed in is of
    the correct marshall type, in which case it may just use that msgbuf.
    """
	def __init__(self, clientType, hub, clientAddress):
		#print "PeerHandler:", self
		self.clientType = clientType
		self.clientAddress = clientAddress
		self.clientDescription = None
		self.hub = hub
		self.pattern = Pattern()
		self.joinTime = time.time()
		self.numSent = 0
		self.numDropped = 0
		self.numReceived = 0
		self.numBadReceived = 0  # Received requests that wouldn't parse
		self.lastSent = None
		self.lastReceived = None
		self.counter = Counter()

	def peerName(self):
		return "%s:%s" % (self.clientType, self.clientAddress)

	def getInfo(self):
		"Generate one line description of this peer handler"
		return "%s Client: %s\n" % (self.clientType, self.peerName())

	def getStats(self, prefix="  "):
		"Generate multi-line information about this peer handler"
		et = time.time() - self.joinTime
		str = prefix + "Started %s (%s)\n" % (time.ctime(self.joinTime), durString(et))
		if self.clientDescription:
			str += prefix + "Description: %s\n" % self.clientDescription
		str += (prefix + "Messages sent to: %d (%d dropped)  received from: %d\n" % \
				(self.numSent, self.numDropped, self.numReceived))
		str += (prefix + "Pattern: %s\n" % self.pattern)
		return str

	def sendMessage(self, msg, msgBuf, marshallType):
		"""
        Send a message to the peer of this handler.
        """
		print "sendMessage not implemented"

	def wrapup(self):
		print "Peer died for..."
		print self.getInfo()
		self.hub.unregisterPeerHandler(self)
		print "Active handlers:"
		self.hub.showInfo(sys.stdout, 0)


class SubscriptionHandler(PeerHandler):
	def __init__(self, clientType, hub, clientAddress, subscriptionId, timeout=None):
		PeerHandler.__init__(self, clientType, hub, clientAddress)
		if timeout == None:
			timeout = SUBSCRIPTION_TIMEOUT
		print "SubscriptionHandler:", subscriptionId
		self.timeout = timeout
		self.maxMessages = 2000
		self.subscriptionId = subscriptionId
		self.creatorInfo = (clientType, clientAddress)
		#	self.lastRetrievalTime = 0  # never retrieved
		self.lastRetrievalTime = time.time()
		self.storedMessages = []

	def checkCurrency(self):
		et = time.time() - self.lastRetrievalTime
		if et > self.timeout:
			print "*** Timout for Subscription:", self.peerName()
			self.wrapup()
			return -1
		return 0

	def peerName(self):
		return self.subscriptionId

	def getStats(self, prefix="  "):
		et = time.time() - self.lastRetrievalTime
		str = PeerHandler.getStats(self, prefix)
		str += prefix + \
			   "Stored Messages: %d  Capacity: %d  Time Since Retrieval: %s   Timeout: %s\n" % \
			   (len(self.storedMessages), self.maxMessages, durString(et), durString(self.timeout))
		str += prefix + "Created by: %s\n" % `self.creatorInfo`
		return str

	def sendMessage(self, msg, msgBuf, marshallType):
		if len(self.storedMessages) < self.maxMessages:
			self.storedMessages.append(msg)
		else:
			print "Overflow for Subscription:", self.peerName()
			self.numDropped += 1
		self.numSent += 1
		self.lastSent = msg
		self.checkCurrency()

	#
	# ***** Note... this should use some form of mutex to
	# protect this close and the sendMessages code above.
	# probably make storedMessages a thread safe queue
	def retrieveStoredMessages(self):
		msgs = self.storedMessages
		# if a message got added in here by another thread it would be lost
		self.storedMessages = []
		self.lastRetrievalTime = time.time()
		return msgs

##############################################################################
#
#  Client Side Base Classes

class Waiter:
	def __init__(self, pattern):
		self.pattern = pattern
		self.queue = Queue.Queue()

# Dummy Base class for Message Client.  Knows how to send a message.
#
# The implementations of MessageClient allow a MessageHandler class
# to be registered which is called for incoming messages.
#
class BaseMessageClient:
	def __init__(self):
		self.rootClient = self
		self.messageHandlers = []
		self.waiters = []
		self.clientName = defaultClientName()
		if verbosity:
			print "ClientName:", self.clientName

	def setName(self, name):
		self.clientName = name

	def sendMessage(self, dict):
		print "****** MessageClient.sendMessage not implemented"
		return -1

	def sendMessages(self, msgs):
		for msg in msgs:
			self.sendMessage(msg)

	def registerMessageHandler(self, messageHandler, patternDict=None):
		if type(patternDict) == type("str"):
			patternDict = {'msgType': patternDict}
		messageHandler = getHandlerObject(messageHandler)
		messageHandler.pattern.addDict(patternDict)
		if not messageHandler in self.messageHandlers:
			self.messageHandlers.append(messageHandler)
		self.sendMetaInfo()

	def unregisterMessageHandler(self, messageHandler):
		self.messageHandlers.remove(messageHandler)
		self.sendMetaInfo()

	def waitForMessage(self, pattern, timeout=1.0E100):
		self.sendMessagesAndWaitForMessage([], pattern, timeout)

	def sendMessagesAndWaitForMessage(self, msgs, pattern, timeout=1.0E100):
		if verbosity > 1:
			print "waitForMessage:", pattern
		thread = threading.currentThread()
		isReaderThread = False
		try:
			if thread.isReaderThread:
				isReaderThread = True
		except:
			pass
		if isReaderThread:
			print "Spawning new ReaderThread()"
			thread.isReaderThread = False
			thread.client.startReaderThread()
		waiter = Waiter(Pattern(pattern))
		self.waiters.append(waiter)
		self.sendMessages(msgs)
		try:
			if verbosity > 1:
				print "Waiting for message..."
			msg = waiter.queue.get(timeout=timeout)
		except:
			msg = None
		self.waiters.remove(waiter)
		if verbosity > 1:
			print "waitForMessage got:", msg
		return msg

	def sendMessageAndWaitForMessage(self, msg, pattern, timeout=1.0E10):
		return self.sendMessagesAndWaitForMessage([msg], pattern, timeout)

	def waitForMessage(self, pattern, timeout=1.0E10):
		return self.sendMessagesAndWaitForMessage([], pattern, timeout)

	def setPollingInterval(self, t):
		pass

	def shutdown(self):
		print "****** MessageClient.shutdown"

	def handleMessages(self, msgs):
		for msg in msgs:
			self.handleMessage(msg)

	def handleMessage(self, msg):
		waiters = self.rootClient.waiters
		for waiter in waiters:
			if waiter.pattern.matches(msg):
				waiter.queue.put(msg)
		for messageHandler in self.messageHandlers:
			if messageHandler.pattern:
				if not messageHandler.pattern.matches(msg):
					continue
			try:
				messageHandler.handleMessage(msg)
			except:
				traceback.print_exc()

	def readMessageFile(self, path, callHandlers=1, sendMessages=0):
		msgs = MessageFile.readMessageFile(path)
		if msgs == None:
			return None
		if callHandlers:
			self.handleMessages(msgs)
		if sendMessages:
			self.sendMessages(msgs)
		return msgs

	def sendMetaInfo(self):
		if verbosity:
			print "BaseMessageClient.sendMetaInfo"

#
# A PeerMessageClient is connection oriented.  It connects to
# a server.  This may provide better performance, and allow
# immediate notification of a server dies.
#
# It also allows handlers to be registered for messages
# returning from the server.
#
# Note that clients and servers are nearly symmetrical.  Both
# can receive messages, and dispatch to a message handler.
# But a server may have many peer clients.
#
class PeerMessageClient(BaseMessageClient):
	def noticeServerClosed(self):
		print "Socket closed"

	def isConnected(self):
		print "Not implemented..."

	def connectToServer(self):
		print "Not implemented..."

	def sendMetaInfo(self):
		if not self.isConnected():
			return
		#print "sendMetaInfo:"
		com = string.join(sys.argv)
		smsg = {'system.msgType': 'clientDescription', 'clientDescription': com}
		self.sendMessage(smsg)
		smsg = {'system.msgType':'pattern.clear'}
		#print "send:", smsg
		self.sendMessage(smsg)
		for h in self.messageHandlers:
			pattern = h.pattern
			for msg in pattern.pmsgs:
				#print "pmsg:", msg
				smsg = copy.copy(msg)
				smsg['system.msgType'] = "pattern.add"
				#print " send:", smsg
				self.sendMessage(smsg)

	def listenForever(self):
		self.running = 1
		while self.running:
			time.sleep(10)

	def shutdown(self):
		self.running = 0


###############################################

import SocketMB
import HTTPMB
import XMLRPCMB


def getHandlerObject(handler):
	if isinstance(handler, SimpleMessageHandler):
		#        print "****** handler already OK *********"
		return handler
	if isinstance(handler, type(lambda:0)) or \
			isinstance(handler, types.MethodType):
		print "***** creating function message handler ****"
		return LambdaMessageHandler(handler)
	print "***** Cannot create handler for object", handler

#
# This may later become a smart client which can have
# serveral differet Client objects, it uses to send
# messages to the right server.  For now it is just
# the default SocketMessageClient.
#
class MessageClient(BaseMessageClient):
	def __init__(self, host=None, port=MESSAGE_BOARD_PORT, name=None, initPath="", marshaller=None):
		BaseMessageClient.__init__(self)
		if name == None:
			name = defaultClientName()
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
		self.clients = []
		self.registerClient(SocketMB.SocketMessageClient(host=host, port=port))
		self.setName(name)
		self.listenForeverThread = None

	def __del__(self):
		print "Deleting MessageClient..."
		time.sleep(1)
		BaseMessageClient.__del__(self)

	def setName(self, name):
		self.clientName = name
		for client in self.clients:
			client.setName(name)

	def dumpInfo(self, ofile = sys.stderr):
		ofile.write("MessageClient (Portal)\n")
		ofile.write("Actual Clients:\n")
		for client in self.clients:
			try:
				ofile.write("Client: %s   isConnected: %d\n" % (`client`, client.isConnected()))
			except:
				ofile.write("Client: %s\n" % `client`)

	def registerClient(self, client, patternMsg={}):
		client.pattern = Pattern(patternMsg)
		client.rootClient = self
		self.clients.append(client)

	def sendCommandLine(self, str):
		"""Experimental feature for sending strings instead of messages to
            be used for protocol control."""
		for client in self.clients:
			client.sendCommandLine(str)

	def setMarshallerType(self, mtype):
		"""Experimental feature for setting marshaller type"""
		for client in self.clients:
			client.setMarshallerType(mtype)

	def sendMessage(self, msg):
		numSent = 0
		if type(msg) in [type("str"), type(u"str")]:
			msg = {'msgType': msg}
		for client in self.clients:
			if not client.pattern.matches(msg):
				continue
			if client.sendMessage(msg) == 0:
				numSent += 1
		if numSent > 0:
			return 0
		return -1

	def makeMessageCall(self, msg, replyType='msg.reply', timeout=None):
		if type(msg) in [type("str"), type(u"str")]:
			msg = {'msgType': msg}
		if verbosity > 0:
			print "-------------------------------"
		if timeout == None:
			timeout = MBRPC_TIMEOUT
		requestId = getRequestId()
		msg['requestId'] = requestId
		replyPattern = {'msgType': replyType, 'requestId': requestId}
		if verbosity > 0:
			print "sending:", msg
			print "waiting for:", replyPattern
		rmsg = self.sendMessageAndWaitForMessage(msg, replyPattern, timeout)
		if verbosity > 0:
			print "got reply:", rmsg
			print "----------------"
		return rmsg

	def registerMessageHandler(self, messageHandler, pattern=None):
		if type(pattern) == type("str"):
			pattern = {'msgType': pattern}
		messageHandler = getHandlerObject(messageHandler)
		BaseMessageClient.registerMessageHandler(self, messageHandler, pattern)
		for client in self.clients:
			client.registerMessageHandler(messageHandler, pattern)

	def unregisterMessageHandler(self, messageHandler):
		BaseMessageClient.unregisterMessageHandler(self, messageHandler)
		for client in self.clients:
			client.unregisterMessageHandler(messageHandler)

	def getClockTime(self):
		return time.time()

	def listenForever(self):
		self.running = 1
		while self.running:
			time.sleep(10)

	def listenForeverInThread(self):
		self.listenForeverThread = threading.Thread(target=listenForever)
		self.listenForeverThread.start()

	def shutdown(self):
		for client in self.clients:
			client.shutdown()
		self.running = 0
		time.sleep(1.5)
		if self.listenForeverThread != None:
			self.listenForeverThread.join()
			self.listenForeverThread = None



def runServers(gatewayClients=[]):
	hub = MessageServerHub()
	for gatewayClient in gatewayClients:
		hub.registerGatewayClient(gatewayClient)
	if PARANOID:
		HTTPMB.PARANOID = 1
		SocketMB.runSocketServer(hub=hub, useThread=1)
		HTTPMB.runHTTPServer(hub=hub, port=80)
	else:
		SocketMB.runSocketServer(hub=hub, useThread=1)
		HTTPMB.runHTTPServer(hub=hub, useThread=1)
		XMLRPCMB.runXMLRPCServer(hub=hub)

def MessageServer():
	hub = MessageServerHub()
	SocketMB.runSocketServer(hub=hub, useThread=1)
	HTTPMB.runHTTPServer(hub=hub, useThread=1)
	XMLRPCMB.runXMLRPCServer(hub=hub, useThread=1)
	return hub

def Portal(name, host=None):
	client = MessageClient(host=host,name=name)
	return client

def HTTPMessageClient(serverHost, port):
	import HTTPMessageClient
	client = HTTPMessageClient.HTTPMessageClient(serverHost, port)
	return client

def SubscriptionClient(*args, **kw):
	import HTTPSubscriptionClient
	client = apply(HTTPSubscriptionClient.HTTPSubscriptionClient, args, kw)
	return client

def SocketMessageClient(serverHost, port):
	import SocketMB
	client = SocketMB.SocketMessageClient(serverHost, port)
	return client

def MCastMessageClient(addr=None, port=None):
	import MCastMessageClient
	client = MCastMessageClient.MCastMessageClient(addr, port)
	return client

class _ShutdownObj:
	""" This is just being used by a mechanism to delay exit slightly
        so that if a programs send just one message, and the user does
        not do a shutdown on the client, the messages really get sent.
        This will delay exit for long enough the messages do get sent.
        It would probably be better for this to shutdown all clients
        but this seems to work.
    """
	def __del__(self):
		#print "******* _ShutdownObj.__del__"
		time.sleep(0.3)
	#print "**** done ****"

_SHUTDOWN_OBJ = _ShutdownObj()

_MB_PORTAL_ = None

def _getTopPortal():
	global _MB_PORTAL_
	if _MB_PORTAL_ == None:
		_MB_PORTAL_ = Portal(DEFAULT_MESSAGE_BOARD_HOST)
	return _MB_PORTAL_

def sendMessage(msg):
	portal = _getTopPortal()
	portal.sendMessage(msg)

def registerMessageHandler(handler, pattern):
	portal = _getTopPortal()
	portal.registerMessageHandler(handler, pattern)

def listenForever(handler=None, pattern=None):
	portal = _getTopPortal()
	if handler:
		portal.registerMessageHandler(handler, pattern)
	portal.listenForever()


class MBRPCProxy:
	def __init__(self, name, mboard="localhost", replyType="msg.reply"):
		if type(mboard) in [type("str"), type(u"str")]:
			mboard = MessageClient(mboard)
		mboard.registerMessageHandler(DummyMessageHandler(), {'msgType': replyType})
		setattr(self, '_mboard', mboard)
		setattr(self, '_name', name)
		setattr(self, '_replyType', replyType)

	def __repr__(self):
		return "MBRPCProxy"

	def __makeCall(self, methodName, **args):
		msg = dict(args)
		msg['msgType'] = methodName
		mboard = self._mboard
		return mboard.makeMessageCall(msg, replyType=self._replyType)

	def __getattr__(self, attr):
		if `attr` == '__str__':
			return 'mbProxy'
		methodName = self._name+"."+attr
		return lambda s=self, mname=methodName, **args: s.__makeCall(mname, **args)


def runMessageBoardServer():
	try:
		# print "DEFAULT_INIT_FILE_PATH:", DEFAULT_INIT_FILE_PATH
		if len(sys.argv) > 1:
			PARANOID = 1
		gatewayClients = []
		if MCAST_GATEWAY:
			mcastGateway = MCastMessageClient()
			gatewayClients.append(mcastGateway)
		runServers(gatewayClients)
	except:
		traceback.print_exc(file=sys.stderr)
		raw_input()


if __name__ == '__main__':
	runMessageBoardServer()


