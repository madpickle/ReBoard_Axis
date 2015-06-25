
import MCastMessageClient

MCastMessageClient.MCAST_LOOPBACK = 1
from MCastMessageClient import *

class MyHandler(SimpleMessageHandler):
    numReceived = 0
    def handleMessage(self, msg):
#	print msg
	self.numReceived += 1
        if msg['msgType'] == 'test.reset':
	    self.numReceived = 0
        elif msg['msgType'] == 'test.dump':
	    print "Num Received:", self.numReceived
	elif msg['msgType'] == 'test.add':
	    pass
	else:
	    print msg

handler = MyHandler()
mbPortal = MCastMessageClient()
mbPortal.registerMessageHandler(handler)
mbPortal.listenForever()



