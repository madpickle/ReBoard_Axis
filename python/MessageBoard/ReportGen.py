
from MessageBoard import *
import MessageBoard
import socket
import time

MINS = 60
HOURS = 60*MINS
DAYS = 24*HOURS

def durString(t):
    if t > DAYS:
	return "%.1f days" % (t / DAYS)
    if t > HOURS:
	return "%.1f hours" % (t / HOURS)
    if t > MINS:
	return "%.1f mins" % (t / MINS)
    return "%d secs" % t

class ReportGenerator:
    def __init__(self, hub):
	self.hub = hub

    def genHandlerInfo(self, handler, ostr):
	ostr.write("%s" % handler.getInfo())
	ostr.write("%s" % handler.getStats())
	if handler.lastSent:
	    ostr.write("  Last Sent To:\n   %s\n" % handler.lastSent)
	if handler.lastReceived:
	    ostr.write("  Last Received From:\n   %s\n" % handler.lastReceived)
	ostr.write("\n")


    def genReport(self, ofile=None):
	if ofile == None:
	    ofile = sys.stdout
	hub = self.hub
	t = time.time()
        hostname = socket.gethostname()
	ofile.write("Status Report for MessageBoard on %s " % hostname)
	ofile.write("(Version %s)\n" % MessageBoard.__version__)
	startTime = hub.startTime
	et = t - startTime
	ofile.write("Started %s (%s)\n" % (time.ctime(startTime), durString(et)))
	ofile.write("Num Received: %d\n" % hub.numReceived)
	ofile.write("%d active clients:\n" % len(hub.peerHandlers))
	for handler in hub.peerHandlers:
	    self.genHandlerInfo(handler, ofile)
        ofile.write("\nMessage Type Summary (with last Message info by type):\n")
        for key in hub.counter.keys():
	    count = hub.counter[key]
	    ofile.write("%7d %s\n" % (count, key))
	    try:
 	        msg = hub.lastMessageByType[key]
                peerName = hub.lastPeerByType[key]
                msgTime = hub.lastTimeByType[key]
                et = t - msgTime
                timeStr = "%s (%s)" % (time.ctime(msgTime), durString(et))
                ofile.write("         %s   %s\n" % (peerName, timeStr))
                ofile.write("         %s\n" % msg)
	    except:
	        print "Error while generating last message info for", key


