
#import simplejson as json
import json
import StringIO

class JSONMarshaller:
    type = "JSON"

    def __init__(self, verbosity=0):
	self.verbosity = verbosity

    def marshalMessages(self, msgs, indent=4):
	return json.dumps(msgs)

    def marshal(self, msg):
	buf = json.dumps(msg)
        if buf[-1:] == "}":
            buf = buf[:-1]+"\n}\n"
	if self.verbosity > 1:
	    print "json.marshal buf:", buf
	return buf

    def unmarshal(self, buf):
	if self.verbosity > 1:
	    print "json.unmarshal buf:", buf
	return json.loads(buf)

    def marshalToFile(self, msgOrList, path):
	if type(msgOrList) in [type([1,2]), type((1,2))]:
	    messages = msgOrList
	else:
	    messages = [msgOrList]
	ofile = open(path, "w")
	ofile.write(str)
	for msg in messages:
            json.dump(ofile, msg)
	ofile.close()

    def unmarshalFromFile(self, path):
	strm = open(path, "r")
	msgs = []
	for line in strm:
	    msg = self.unmarshal(line)
	    msgs.append(msg)
	if len(msgs) == 1:
	    return msgs[0]
	return msgs

def test():
    m = JSONMarshaller()
    msg1 = {'a': 25, 'b': 40}
    msg2 = {'alpha': 25, 'beta':[1,2,3], 'gamma':(2,3,4)}
    msgs = [msg1, msg2]
    for msg in msgs:
        print "msg:", msg
        buf = m.marshal(msg)
        print "buf:", buf
        rmsg = m.unmarshal(buf)
        print "rmsg:", rmsg
        print "--------------"
    print
    buf = m.marshalMessages([])
    print "buf([]):", buf
    print "msgs:", msgs
    buf = m.marshalMessages(msgs)
    print "marshalledMessages:\n", buf
    rmsgs = m.unmarshal(buf)
    print "rmsgs:", rmsgs
    buf = m.marshal(msgs)
    print "buf:", buf
    rmsgs = m.unmarshal(buf)
    print "rmsgs:", rmsgs

#    msgs = m.unmarshalFromFile("Notes1.xml")
#    print msgs
#    m.marshalToFile(msgs, "Messages1.xml")

if __name__ == '__main__':
    test()

