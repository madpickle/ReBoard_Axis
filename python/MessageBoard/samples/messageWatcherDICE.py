import sys, time
sys.path.append("../")

from MessageBoard import *

MESSAGEBOARD_HOST = "mbserver"

class Handler(SimpleMessageHandler):
    def handleMessage(self, msg):
        print "Message Received: " + time.asctime()
	#print msg 
	if msg.has_key('msgType'):
	   print "msgType: " + msg['msgType']
	if msg.has_key('room'):
	   print "room: " + msg['room']
	if msg.has_key('meeting'):
	   print "meeting: " + msg['meeting']
	if msg.has_key('object'):
	   print "object: " + msg['object']
	print "\n"

client = MessageClient(MESSAGEBOARD_HOST)
patternDict = {}
patternDict['msgType'] = "dice.*"
client.registerMessageHandler(Handler(), patternDict)
print "DICE MessageBoard Clinet sample is started: " + time.asctime()
client.listenForever()
