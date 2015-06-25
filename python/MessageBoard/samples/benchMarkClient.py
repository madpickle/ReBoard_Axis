
import os,sys
sys.path.append('../../')


from MessageBoard import MessageBoard

client = MessageBoard.MessageClient()

n=0
while 1:
    n += 1
    print n
    client.sendMessage({'msgType':'benchMark', 'n':n})

