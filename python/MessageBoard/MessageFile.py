
import string, traceback
import MessageBoard

def readMessageFile(path):
    infile = open(path, 'r')
    buf = ''
    lineNo = 0
    msgs = []
    while 1:
        lineNo += 1
        line = infile.readline()
	if line == None or line == '':
	    break
	if line[:1] == '#':
	    continue
        buf += line
        try:
            i = string.index(line, "}\n")
        except ValueError:
	    continue
        try:
#	    buf = buf.replace('\n', '')
            dict = eval(buf)
	    msgs.append(dict)
	    buf = ""
	except:
	    traceback.print_exc()
	    print "Bad message ending on line %d in %s: %s" % (lineNo, path, buf)
            infile.close()
	    return
    infile.close()
    return msgs

def writeMessageFile(path, msgs, marshaller=None):
    if marshaller == None:
	marshaller = MessageBoard.PythonMarshaller()
    ofile = open(path, 'w')
    for msg in msgs:
        str = marshaller.marshal(msg)
	ofile.write(str)
    ofile.close()

if __name__ == '__main__':
    msgs = readMessageFile("test.msgs")
    for msg in msgs:
        print msg
    writeMessageFile("testout.msgs", msgs)
    writeMessageFile("testout.xml", msgs, MessageBoard.XMLMarshaller())


