
import MessageBoard
import time

DEFAULT_MESSAGE_BOARD_HOST = "localhost"
BROADCAST_STATE = True
verbosity = 0

class SharedDict:
    def __init__(self, objectId, osClient, server=None):
	self.objectId = objectId
	self.osClient = osClient
	self.server = server
	self.dict = {}
        self.lastReplyTime = -1

    def __getitem__(self, key):
	return self.dict[key]

    def __setitem__(self, key, val):
	self.dict[key] = val
	self._sendState()

    def setProps(self, dict):
        for key in dict.keys():
	    self.dict[key] = dict[key]
	self._sendState()

    def _sendState(self):
	msg = dict(self.dict)
	msg['msgType'] = 'store.setState'
	msg['objectId'] = self.objectId
	self.osClient.mbPortal.sendMessage(msg)
	if self.server:
	    self.server.storeState(self, dict)

    def __repr__(self):
	return self.dict.__repr__()


class ObjectShare(MessageBoard.SimpleMessageHandler):
    def __init__(self, mbPortal = None):
	MessageBoard.SimpleMessageHandler.__init__(self)
	if mbPortal == None:
	    mbPortal = MessageBoard.MessageClient(DEFAULT_MESSAGE_BOARD_HOST)
	self.mbPortal = mbPortal
	self.objects = {}


class ObjectShareClient(ObjectShare):
    def __init__(self, mbPortal = None):
	ObjectShare.__init__(self, mbPortal)
	self.clientId = self.mbPortal.clientName
        replyPattern = {'msgType':'reply.*', 'clientId': self.clientId}
        self.mbPortal.registerMessageHandler(self, replyPattern)
        self.mbPortal.registerMessageHandler(self, {'msgType': 'store.setState'})
        self.mbPortal.registerMessageHandler(self, {'msgType': 'store.setProps'})

    def handleMessage(self, msg):
	if verbosity > 1:
	    print msg
	msgType = msg['msgType']
	if msgType == 'store.setState':
	    self.handleSetPropsMsg(msg)
	    return
	if msgType == 'store.setProps':
	    self.handleSetPropsMsg(msg)
	    return
	if msgType == 'reply.finish':
	    return
	print "Unrecognized Message:", msg

    def handleSetPropsMsg(self, msg):
	objId = msg['objectId']
        if not self.objects.has_key(objId):
	    return
	obj = self.objects[objId]
	for key in msg.keys():
	    if key in ['objectId', 'msgType']:
	        continue
	    obj.dict[key] = msg[key]
	return obj

    def getObject(self, objId):
        if self.objects.has_key(objId):
	    obj = self.objects[objId]
        else:
	    if verbosity:
               print "Creating Object:", objId
	    obj = SharedDict(objId, self)
	    self.objects[objId] = obj
	    self.initializeState(obj)
        return obj

    def initializeState(self, obj, timeout=5):
        msg = {'msgType':'store.getState',
	       'objectId': obj.objectId,
	       'clientId': self.clientId}
        replyPattern = {'msgType':'reply.finish', 'clientId': self.clientId}
#	self.mbPortal.sendMessageAndWaitForMessage(msg, replyPattern)
        print "sending:", msg
	self.mbPortal.sendMessage(msg)
        print "waiting for:", replyPattern
        replyMsg = self.mbPortal.waitForMessage(replyPattern, timeout)
        print "got reply:", replyMsg
        self.handleReply(replyMsg)

    def handleReply(self, msg):
	if verbosity:
	    print msg
	objId = msg['objectId']
	obj = self.getObject(objId)
	for key in msg.keys():
            if key in ['objectId', 'msgType', 'clientId']:
	       continue
	    obj.dict[key] = msg[key]
	obj.lastReplyTime = time.time()


class ObjectShareServer(ObjectShare):
    def __init__(self, mbPortal=None, objPattern={}):
	ObjectShare.__init__(self, mbPortal)
	pattern = dict(objPattern)
	pattern['msgType'] = 'store.*'
	if not pattern.has_key("objectId"):
	    pattern['objectId'] = 'object*'
	print "***************************************"
	print "Serving objects messages matching:"
	print pattern
	print "***************************************"
	self.mbPortal.registerMessageHandler(self, pattern)

    def getObject(self, objId):
        if self.objects.has_key(objId):
	    obj = self.objects[objId]
        else:
	    if verbosity:
               print "Creating Object:", objId
	    obj = SharedDict(objId, self, self)
	    self.initializeObject(obj)
	    self.objects[objId] = obj
        return obj

    def initializeObject(self, obj):
	pass

    def handleMessage(self, msg):
	if verbosity > 0:
            print msg
        msgType = msg['msgType']
	if msgType == 'store.getState':
	    self.handleGetStateMsg(msg)
	    return
	if msgType == 'store.setState':
	    self.handleSetPropsMsg(msg)
	    return
	if msgType == 'store.setProps':
	    self.handleSetPropsMsg(msg)
	    return
	if msgType == 'store.dump':
	    self.dump(msg)
	    return
	print "Unrecognized Message:", msg

    def handleSetPropsMsg(self, msg):
	objId = msg['objectId']
	obj = self.getObject(objId)
        vals = dict(msg)
	del vals['objectId']
	del vals['msgType']
	self._setProps(obj, vals)
        if BROADCAST_STATE:
            self.broadcastState(objId)
	return obj

    # We should get rid of this, and have the overloading by servers
    # be on the storeProps method
    #
    def _setProps(self, obj, dict):
	obj.setProps(dict)

    def storeState(self, obj, dict):
	pass

    def broadcastState(self, objId):
        print "Broadcasting state"
	obj = self.getObject(objId)
	objMsg = dict(obj.dict)
        objMsg['objectId'] = objId
        objMsg['msgType'] = 'object.noticeState'
        self.mbPortal.sendMessage(objMsg)

    def handleGetStateMsg(self, msg):
	objId = msg['objectId']
	clientId = msg['clientId']
	obj = self.getObject(objId)
	objMsg = dict(obj.dict)
        objMsg['objectId'] = objId
        objMsg['msgType'] = 'reply.finish'
        objMsg['clientId'] = clientId
        self.mbPortal.sendMessage(objMsg)

    def run(self):
	self.mbPortal.listenForever()
        
    def dump(self, msg=None):
	print "-------------------------------------------------"
	for id in self.objects.keys():
	    print "%s:" % id
	    print self.objects[id]
	print "-------------------------------------------------"

###############################################################################
#
# XMLRPC Support
#
import xmlrpclib
import SimpleXMLRPCServer
import threading

OBJECTSHARE_XMLRPC_PORT = 9020

def getXMLRPCServer(mbClient=None):
    server_address = ('', OBJECTSHARE_XMLRPC_PORT)
    xserver = SimpleXMLRPCServer.SimpleXMLRPCServer(server_address)
    return xserver

class ObjectShareXMLRPCServer:
    def __init__(self, objectShareServer):
	self.objectShareServer = objectShareServer

    def setProps(self, objectId, dict):
	if verbosity > 1:
	    print "XMLRPC setProps", objectId, dict
	obj = self.objectShareServer.getObject(objectId)
	self.objectShareServer._setProps(obj, dict)
	return obj.dict

    def getState(self, objectId):
	if verbosity > 1:
	    print "XMLRPC getState", objectId
	obj = self.objectShareServer.getObject(objectId)
	return obj.dict


def runObjectShareXMLRPCServer_(objectShareServer):
    xserver = getXMLRPCServer(objectShareServer.mbPortal)
    osxs = ObjectShareXMLRPCServer(objectShareServer)
    xserver.register_instance(osxs)
    print "Running XMLRPC ObjectShare on port", OBJECTSHARE_XMLRPC_PORT
    xserver.serve_forever()

def runObjectShareXMLRPCServer(objectShareServer, useThread=1):
    if useThread:
        thread = threading.Thread(target=runObjectShareXMLRPCServer_, args=(objectShareServer,))
        thread.setDaemon(1)
        thread.start()
        return thread
    else:
        runObjectShareXMLRPCServer(objectShareServer)


#######################################################################################
#
#   Client side
#

class XMLRPCSharedDict(SharedDict):
    def __init__(self, objectId, osClient, xserver):
	SharedDict.__init__(self, objectId, osClient)
	self.server = xserver

    def getState(self):
	self.dict = self.server.getState(self.objectId)

    def _sendState(self):
	self.server.setProps(self.objectId, self.dict)

class ObjectShareXMLRPCClient(ObjectShareClient):
    def __init__(self, hostname=None):
	ObjectShareClient.__init__(self)
	hostname=None
        if hostname == None:
	    hostname = "localhost"
        port = OBJECTSHARE_XMLRPC_PORT
        self.server = xmlrpclib.Server("http://%s:%d" % (hostname, port))

    def getObject(self, objId):
        if self.objects.has_key(objId):
	    obj = self.objects[objId]
        else:
	    if verbosity:
               print "Creating Object:", objId
	    obj = XMLRPCSharedDict(objId, self, self.server)
	    obj.getState()
	    self.objects[objId] = obj
        return obj


def play():
    global oc, yodel, box
    """
    oc = ObjectShareClient()
    yodel = oc.getObject('yodel')
    box = oc.getObject('box')
    """
    xoc = ObjectShareXMLRPCClient()
    box = xoc.getObject('box')

if __name__ == '__main__':
    verbosity = 2
    os = ObjectShareServer()
    runObjectShareXMLRPCServer(os)
    os.run()

