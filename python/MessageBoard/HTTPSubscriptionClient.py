
from MessageBoard import *
from HTTPMB import *
import socket, urllib, urllib2, httplib, traceback

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

#
# Should be more careful to make sure its really unique
#
def getUniqueId():
    host = socket.gethostname()
    t = time.time()
    return "%s_%.3f" % (host, t)


class HTTPSubscriptionClient(PeerMessageClient):
    def __init__(self, host=None, port=MESSAGE_BOARD_HTTP_PORT,
			 initPath="", marshaller=None,
			 fetchInterval=4,
			 subscriptionId="", subscriptionTimeout=5*60):
	PeerMessageClient.__init__(self)
        if marshaller == None:
            marshaller = Marshaller()
        self.marshaller = marshaller
	if subscriptionId == "":
	    subscriptionId = getUniqueId()
	self.subscriptionId = subscriptionId
	self.subscriptionTimeout = subscriptionTimeout
	if initPath == "" and os.path.exists(DEFAULT_INIT_FILE_PATH):
	    initPath = DEFAULT_INIT_FILE_PATH
	dict = {}
	self.raiseExceptions = 0
	if initPath:
	    dict = readParamFile(initPath)
	self.verbosity = 0
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
	self.fetchInterval = fetchInterval
	self.httpStream = None
	self.subscribed = 0
	self.connected = 0
	self.sendSubscriptionInfo()
        print "Creating listener thread..."
	sys.stdout.flush()
	self.running = 1
        self.thread = threading.Thread(target = self.listener, args=(self,))
	self.thread.setDaemon(1)
	self.thread.start()

    def setPollingInterval(self, t):
	if t != self.fetchInterval:
	    print "Setting Polling Interval:", t
	self.fetchInterval = t

    def sendSubscriptionInfo(self):
        msg = {'system.msgType':'subscribe',
	       'system.subscriptionTimeout': self.subscriptionTimeout,
	       'system.subscriptionId': self.subscriptionId}
        print "Sending Subscription Message:", msg
	rc = self.sendMessage(msg)
	if rc < 0:
            print "failed"
	    self.subscribed = 0
	else:
            print "succeeded"
            self.subscribed = 1

    def isConnected(self):
	return self.connected != 0

    def connectToServer(self):
	if self.verbosity:
            print "Attempting to connect to %s:%d..." % (self.host, self.port)
	try:
	    fetchUrl = "http://%s:%d/fetchMessages?subscriptionId=%s" % \
			(self.host, self.port, self.subscriptionId)
	    if self.verbosity:
	        print "GET", fetchUrl
            self.httpStream = urllib2.urlopen(fetchUrl)
	    line = self.httpStream.readline()
            try:
                string.index(line, "Error:")
                self.httpStream = None
	        self.connected = 0
	    except:
	        pass
	    #print "Line 1:", line
	    line = self.httpStream.readline()
	    #print "Line 2:", line
	    self.connected = 1
	    if self.verbosity:
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
	      while not self.subscribed:
		  self.sendSubscriptionInfo()
		  self.sendMetaInfo()
	          self.sleep(self.fetchInterval)
	      self.connectToServer()
	      if self.httpStream == None:
	          self.subscribed = 0
	          self.sleep(self.fetchInterval)
	   try:
	      self.readMessages()
	   except NoServerException:
	      pass
	   except:
              traceback.print_exc(file=sys.stderr)
	   self.sleep(self.fetchInterval)
        print "listener exiting..."

    def sleep(self, t):
        i = 0                         # do it this way so
	while i < self.fetchInterval: # if the interval is long
	    time.sleep(1)             # and gets set low, we
	    i += 1                    # wake up quickly

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
	raise NoServerException

    def sendMetaInfo(self):
	smsgs = []
	print "sendMetaInfo:"
	smsg = {'system.msgType':'pattern.clear',
	        'system.subscriptionId':self.subscriptionId}
	smsgs.append(smsg)
	for h in self.messageHandlers:
	    pattern = h.pattern
	    for msg in pattern.pmsgs:
	        smsg = copy.copy(msg)
	        smsg['system.msgType'] = "pattern.add"
	        smsg['system.subscriptionId'] = self.subscriptionId
		#print " send:", smsg
	        smsgs.append(smsg)
	self.sendMessages(smsgs)

    def sendMessageUsingGET(self, dict):
	str = urlEncode(dict)
	url = "http://%s:%d/sendMessage?%s" % (self.host, self.port, str)
	if self.verbosity:
	    print url
	try:
   	    uos = urllib2.urlopen(url)
	    uos.close()
	    return 0
	except:
            traceback.print_exc(file=sys.stderr)
	    print "Couldn't send message"
	    return -1

    """
    def sendMessageUsingPOST(self, dict):
	print "SendUsing POST", dict
	url = "http://%s:%d/postMessage" % (self.host, self.port)
	data = urllib.urlencode(dict)
	req = urllib2.Request(url, data)
	try:
   	    uos = urllib2.urlopen(req)
	    uos.close()
	except:
            traceback.print_exc(file=sys.stderr)
	    print "Couldn't send message"
    """
    def sendMessageUsingPOST(self, dict):
	if self.verbosity:
	    print "SendUsing POST"
	server = "%s:%d" % (self.host, self.port)
	data = urllib.urlencode(dict)
	data += "\n"
	dataLen = len(data)
        headers = {"Content-type": "application/x-www-form-urlencoded",
		   "Content-length": `dataLen`}
	try:
            conn = httplib.HTTPConnection(server)
            conn.request("POST", "/postMessage", data, headers)
            response = conn.getresponse()
            print response.status, response.reason
	    str = response.read()
            #print "str:", str
            conn.close()
	    return 0
	except:
            traceback.print_exc(file=sys.stderr)
	    print "Couldn't send message"
	    return -1

    def sendMessage(self, dict):
	#self.sendMessageUsingPOST(dict)
	return self.sendMessageUsingGET(dict)

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
    client = HTTPSubscriptionClient(hostname)
    pattern = {'msgType':'chat.*'}
    client.registerMessageHandler(handler, pattern)
    client.sendMessage({'msgType':'chat.test', 'value':'hello', 'num':1})
    # Should not see, because it doesn't match
    client.sendMessage({'msgType':'test', 'value':'hello', 'num':25})
    client.sendMessage({'msgType':'chat.test', 'value':'world', 'num':2})
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

