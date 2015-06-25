
from MessageBoard import *


###############################################################################
#
# XMLRPC Support
#
import xmlrpclib
import SimpleXMLRPCServer

class XMLRPCListener(PeerHandler):
    def __init__(self, hub, url):
	PeerHandler.__init__(self, "XMLRPC", hub, url)
	self.url = url
	self.hub.registerPeerHandler(self)
	self.xmlrpcServer = xmlrpclib.Server(url)

    def sendMessage(self, msg, msgbuf, marshallType):
	print msg
	if msg == None:
	    try:
	       msg = eval(msgbuf)
	    except:
	       print "XMLRPCListener.sendMessage: Cannot get Message dictionary from strng"
	try:
            self.xmlrpcServer.handleMessage(msg)
	    self.numSent += 1
	    return
	except IOError:
	    print "peer Died..."
	    raise IOError
	except:
            traceback.print_exc(file=sys.stderr)
	    print "Failed on:", msg
	    raise IOError

class XMLRPCGateway(Gateway):
    def __init__(self, hub):
        self.hub = hub

    def registerXMLRPCListener(self, url):
	handler = XMLRPCListener(self.hub, url)
	return 0

    def postMessage(self, dict):
	print "XMLRPCGateway:postMessage:", dict
        if self.hub:
             print "propagating..."
             ms = Marshaller()
             msgbuf = ms.marshal(dict)
             self.hub.handleMessage(None, dict, msgbuf, ms.type)
	return 0

def runXMLRPCServer_(hub):
    server_address = ('',MESSAGE_BOARD_XMLRPC_PORT)
    xserver = SimpleXMLRPCServer.SimpleXMLRPCServer(server_address)
    gw = XMLRPCGateway(hub)
    xserver.register_instance(gw)
    print "Running XMLRPC gateway on port", MESSAGE_BOARD_XMLRPC_PORT
    xserver.serve_forever()

def runXMLRPCServer(hub, useThread=0):
    if useThread:
        thread = threading.Thread(target=runXMLRPCServer_, args=(hub,))
        thread.setDaemon(1)
        thread.start()
        return thread
    else:
        runXMLRPCServer_(hub)

