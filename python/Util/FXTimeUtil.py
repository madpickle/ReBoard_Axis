import os,sys
import time, datetime

#convert epochtime (sec) to date time string (YYYYMMDDHHMMSS)
def T2DateString(v):
    tStrf = time.localtime(v)
    tStr = time.strftime("%Y%m%d%H%M%S", tStrf)
    return tStr

def DateString2T(tStr):
    dTime = time.strptime(tStr, "%Y%m%d%H%M%S")
    return int(time.mktime(dTime))

def getT():
    return time.time()

def floorTime(v, interval):
    s = int(v/interval)
    return int(s * interval)

