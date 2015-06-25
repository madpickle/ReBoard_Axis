
import os,sys
sys.path.append('../../')

from MessageBoard import MessageBoard

class Handler(MessageBoard.SimpleMessageHandler):
    def handleMessage(self, msg):
        print "out: %s" % msg['text']

def runChat():
    client = MessageBoard.MessageClient()
    client.registerMessageHandler(Handler(), {'msgType': 'demo.chat.addTextLine'})
    client.dumpInfo()
    while 1:
        print "input: ",
        line = raw_input()
        client.sendMessage({'msgType':'demo.chat.addTextLine', 'text':line})

runChat()

