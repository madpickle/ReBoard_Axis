
from MessageBoard import *

class Handler(SimpleMessageHandler):
    def handleMessage(self, msg):
        print msg

client = MessageClient("localhost")
client.registerMessageHandler(Handler())
client.listenForever()
