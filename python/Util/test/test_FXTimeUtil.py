import os,sys

sys.path.append('../')

import FXTimeUtil


t = FXTimeUtil.getT()
print "current time (epoch sec): " + str(t)

tStr = FXTimeUtil.T2DateString(t)
print "DateString: " + tStr

t = FXTimeUtil.DateString2T(tStr)
print "current time again (epoch sec): " + str(t)




