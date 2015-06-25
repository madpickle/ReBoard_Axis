
import xml.dom.minidom

class XMLMarshallerType2:
    def marshal(self, msgOrList):
	if type(msgOrList) == type([1,2]):
	    messages = msgOrList
	    haveList = 1
	    str = '<messages>\n'
	else:
	    messages = [msg]
	    haveList = 0
	    str = ''
	for msg in messages:
            str += ' <message>\n'
	    for key in msg.keys():
	        str += '  <%s>%s</%s>\n' % (key, msg[key], key)
            str += ' </message>\n'
	if haveList:
	    str += '</messages>\n'
        return str

    def unmarshal(self, buf):
	messages = []
        dom = xml.dom.minidom.parseString(buf)
        messageNodes = dom.getElementsByTagName("message")
        for messageNode in messageNodes:
            msg = {}
            for node in messageNode.childNodes:
                if node.nodeType != node.ELEMENT_NODE:
	            continue
                name = node.nodeName
	        value = node.firstChild.nodeValue
                msg[name] = value
	    messages.append(msg)
        dom.unlink()
	if len(messages) == 1:
	    return messages[0]
	return messages

    def marshalToFile(self, msgOrList, path):
	str = self.marshal(msgOrList)
	ofile = open(path, "w")
	ofile.write('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
	ofile.write(str)
	ofile.close()

    def unmarshalFromFile(self, path):
	str = open(path, "r").read()
	return self.unmarshal(str)


def test():
    m = XMLMarshallerType2()
    msgs = m.unmarshalFromFile("Notes2.xml")
    print msgs
    m.marshalToFile(msgs, "Messages2.xml")

if __name__ == '__main__':
    test()

