
import os,sys
sys.path.append('../')

import MessageBoard
import sys, socket

name = socket.gethostname()
if len(sys.argv) > 1: name = sys.argv[0]

client = MessageBoard.MessageClient()

while 1:
    sys.stderr.write("input: ")
    line = raw_input()
    client.sendMessage({'msgType':'demo.chat.addTextLine',
	                'name':name, 'text':line})

