
import oscAPI
from array import array

def sendMessageToOSC(msg, host="localhost", port=9000):
    args = []
    for key in msg.keys():
        args.append(key)
        args.append(msg[key])
    print "args:", args
    oscAPI.sendMsg("/messageBoardGateway", args, host, port)

if __name__ == '__main__':
    oscAPI.init()
    msg = {'msgType': 'test.type1', 'num': 3, 'vec': (1,2,3.3)}
    sendMessageToOSC(msg, "localhost", 9000)

    msg = {'msgType': 'test.type1', 'num': 3, 'vec': {'a':3.3}}
    sendMessageToOSC(msg, "localhost", 9000)

    msg = {'msgType': 'test.type1', 'num': 3, 'vec': {'a':3.3},
           'n': 5, 'm':0.1,
           'array': array('f', [1,2,3])}
    sendMessageToOSC(msg, "localhost", 9000)


