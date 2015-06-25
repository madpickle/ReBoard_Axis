
import MessageBoard
import oscAPI, socket

def createListener(ipAddr, port):
    """create and return an inbound socket
    """
    l = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    l.bind((ipAddr, port))
#    l.setblocking(0) # if not waits for msgs to arrive blocking other events
#    l.setblocking(1) # if not waits for msgs to arrive blocking other events
    return l

class MB_OSC_Gateway(MessageBoard.SimpleMessageHandler):
    def __init__(self, mbHost="localhost",
                 oscOutHost="localhost", oscOutPort=9000,
                 oscInPort=9001,
                 mbPattern=None):
	MessageBoard.SimpleMessageHandler.__init__(self)
        oscAPI.init()
	self.oscInPort = oscInPort
	self.oscOutPort = oscOutPort
	self.oscOutHost = oscOutHost
        self.mbPortal = MessageBoard.MessageClient(mbHost)
	self.oscInSocket = createListener("localhost", oscInPort)
	if mbPattern:
	    self.mbPortal.registerMessageHandler(self, mbPattern)
	else:
	    self.mbPortal.registerMessageHandler(self)

    def run(self):
        def handleOSCMsg(msg, source, s=self):
            """deals with "print" tagged OSC addresses """
#            print "source:", source
#            print "the oscaddress is ", msg[0]
#            print "the value is ", msg[2]
	    s.handleOSCMessage(source, msg)

        oscAPI.bind(handleOSCMsg, "/messageBoardGateway")
	oscAPI.getOSC(self.oscInSocket)
#	self.mbPortal.listenForever()

    def handleOSCMessage(self, source, oscMsg):
	print "handleOSCMessage", oscMsg
        oscAddress = oscMsg[0]
        oscSignature = oscMsg[1]
        args = oscMsg[2:]
        msg = {}
        while args:
	    msg[args[0]] = args[1]
            args = args[2:]
	print "msg:", msg
	self.mbPortal.sendMessage(msg)

    def handleMessage(self, msg):
	print "Got message from MB:", msg
	self.sendMessageToOSC(msg, self.oscOutHost, self.oscOutPort)

    def sendMessageToOSC(self, msg, host="localhost", port=9000):
        args = []
        for key in msg.keys():
            args.append(key)
            args.append(msg[key])
        print "args:", args
        oscAPI.sendMsg("/messageBoardGateway", args, host, port)


if __name__ == '__main__':
    gateway = MB_OSC_Gateway()
    gateway.run()

