
import time, MessageBoard

client = MessageBoard.MessageClient()

numMessages = 1000
t0 = time.time()
for n in range(numMessages):
    client.sendMessage({'msgType':'benchMark', 'n':n})
t1 = time.time()
print "Num Messages:", numMessages
print "Time:", t1-t0
print "Msgs / sec:", numMessages / (t1-t0)
raw_input()

