
import xml.dom.minidom

class XMLMarshallerType1:
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
	        str += '  <field>\n'
                str += '    <name>%s</name>\n' % key
	        str += '    <value>%s</value>\n' % msg[key]
	        str += '  </field>\n'
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
            for field in messageNode.getElementsByTagName("field"):
                nameNode = field.getElementsByTagName("name")[0]
   	        name = nameNode.firstChild.nodeValue
    	        valueNode = field.getElementsByTagName("value")[0]
   	        value = valueNode.firstChild.nodeValue
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
    m = XMLMarshallerType1()
    msgs = m.unmarshalFromFile("Notes1.xml")
    print msgs
    m.marshalToFile(msgs, "Messages1.xml")

if __name__ == '__main__':
    test()

