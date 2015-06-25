
from oscAPI import *

def createListener(ipAddr, port):
    """create and return an inbound socket
    """
    l = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    l.bind((ipAddr, port))
#    l.setblocking(0) # if not waits for msgs to arrive blocking other events
#    l.setblocking(1) # if not waits for msgs to arrive blocking other events
    return l


def listen():
    init()
    inSocket = createListener("localhost", 9000)

    # add addresses to callback manager
    def printStuff(msg, source):
        """deals with "print" tagged OSC addresses """

        print "printing in the printStuff function ", msg
        print "source:", source
        print "the oscaddress is ", msg[0]
        print "the value is ", msg[2]

#    bind(printStuff, "/test")
    bind(printStuff, "/messageBoardGateway")
#    bind(printStuff, "/testing/bundles")

    # receive OSC
    getOSC(inSocket)


listen()





