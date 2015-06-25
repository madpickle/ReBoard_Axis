
import time, sys
import MBDB.DB

HOUR = 3600
DAY = 24*HOUR

msgType = "cin.status"
msgType = "sound.direction"
t = time.time()
tStart = t-30*DAY
#tEnd = tStart + 1*DAY
tEnd = t

mdb = MBDB.DB.MessageBoardDB(host="epic1")
mdb.counts()
mdb.delete("sound.direction")
mdb.counts()
sys.exit(0)
t0 = tStart
n = 0
while t0 <= tEnd:
   t1 = t0 + 1*HOUR
   n += 1
   #mdb.delete(msgType, t0, t1)
   mdb.delete("cin.status", t0, t1)
   mdb.delete("sound.direction", t0, t1)
   t0 = t1
   if n % 10 == 0:
	mdb.counts()

mdb.counts()
t = time.time()
num = 10
mdb.deleteMessages(msgType, num)
t2 = time.time()
dt = t2 - t
print "Elapsed Time:", dt
print "Num Deleted: ", num
print "Dels / Sec: ", num / dt
mdb.counts()

