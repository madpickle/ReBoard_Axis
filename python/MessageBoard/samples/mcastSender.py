from time import *
import MCastMessageClient
MCastMessageClient.MCAST_LOOPBACK = 1
portal = MCastMessageClient.MCastMessageClient()
nMsgs = 25000
t0 = time()
portal.sendMessage({'msgType': 'test.reset'})
for i in range(nMsgs):
    portal.sendMessage({'msgType': 'test.add', 'i': i})
portal.sendMessage({'msgType': 'test.dump'})
t1 = time()
print "sent %d messages in %.3f sec (%f msgs/sec)" % \
          (nMsgs, t1-t0, nMsgs/(t1-t0))
input("any key to finish")

