
import xmlrpclib
import SimpleXMLRPCServer

#
# Define handler and setup server.
#
class Handler:
    def handleMessage(self, msg):
	print msg
	return 0

server_address = ('localhost', 9501)
xserver = SimpleXMLRPCServer.SimpleXMLRPCServer(server_address)
xserver.register_instance(Handler())

#
# Get connection to MessageBoard server and register ourself...
#
s = xmlrpclib.Server("http://localhost:9500")
dict = s.postMessage({'msgType':'test.text', 'text':'Hello World', 'a':20, 'b':3})
s.registerXMLRPCListener("http://localhost:9501")

xserver.serve_forever()




