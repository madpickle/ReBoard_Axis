
import MessageBoard

class MessageLogger(MessageBoard.SimpleMessageHandler):
    def __init__(self, logFilePath="messages.log"):
        MessageBoard.SimpleMessageHandler.__init__(self)
        self.logFilePath = logFilePath
        self.logFile = open(self.logFilePath, "w")
        
    def handleMessage(self, msg):
        print msg
	self.logFile.write('%s\n' % `msg`)

client = MessageBoard.MessageClient()
client.registerMessageHandler(MessageLogger())
client.listenForever()



