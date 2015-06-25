
import time, sys
import MBDB.DB

mdb = MBDB.DB.MessageBoardDB(host="epic1")
mdb.stats()

#mdb = MBDB.MessageBoardDB()
pattern = {'msgType':'cin.*', 'cameraName':'spec2'}
pattern = {'msgType':'cin.setView', 'cameraName':'spec2'}
pattern = {'msgType':'sound.direction'}
pattern = {'msgType':'video.faceDetector'}
t = time.time()
t = 1111198930
t0 = t - 65*60
#t1 = t0 + 200*60
t1 = t
#mdb.dump(pattern, t0, t1)
#mdb.dump(pattern)
#mdb.dump()
print "T0:", t0
print "T1:", t1

"""
#for msgType in ['video.faceDetector', 'cin.status', 'cin.setView']:
for msgType in ['video.faceDetector', 'ePic*']:
   print "------------------"
   print "msgType:", msgType
   msgs = mdb.fetchLast(msgType)
   print msgs
"""

#print "----------------------------------"
#mdb.dump({'msgType':'ePic*'})
#tups = mdb.dump({'msgType':'video.faceDetector'})
mdb.dump({'msgType':'video.faceDetector'}, out=open("faces.msgs","w"))




