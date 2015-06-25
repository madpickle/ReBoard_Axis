import os,sys
sys.path.append('../')

import MessageBoard

class ChatMessageHandler(MessageBoard.SimpleMessageHandler):
    def handleMessage(self, msg):
        if msg.has_key('name'):
            print "%s: %s" % (msg['name'], msg['text'])
        else:
            print "%s" % msg['text']

client = MessageBoard.MessageClient()
client.registerMessageHandler(ChatMessageHandler(), {'msgType':'demo.chat.addTextLine'})
client.listenForever()
