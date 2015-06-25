import sys, string, time
sys.path.append("../")
import MessageBoard
import ObjectShare
MessageBoard.verbosity = 2
ObjectShare.verbosity = 2
#oc = ObjectShare.ObjectShareClient()
oc = ObjectShare.ObjectShareXMLRPCClient()
ob=oc.getObject("DBbench")

n=0
t0 = time.time()
while n<1000:
    n += 1
    #print n
    t = time.time()
    ob.setProps({'sendtime': t, 'n': n, 'msg': 'testing', 'm': 100+n, '2fsdaf': 200-n})
    #ob['sendtime'] = t
    #ob['n'] = n
    #ob['msg'] = "testing"
    #ob['m'] = 100+n
    #ob['2fsdaf'] = 200 - n

print "sendtime:" , (t-t0)
time.sleep(20)

    
