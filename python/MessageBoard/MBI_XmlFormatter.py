import sys, string, StringIO
import xml.dom.minidom

from MBI import *

class Formatter:
    """
    marshaller
    """
    def marshal_field(self, fdef, os=sys.stdout):
	os.write("<field>\n");
	os.write("<name>%s</name>\n" %fdef.name);
	os.write("<ftype>%s</ftype>\n" % fdef.ftype);
	if fdef.optional:
		os.write("<optional>True</optional>\n");
	if fdef.default:
		os.write("<default>%s</default>\n" % fdef.default);
	if fdef.value:
		os.write("<value>%s</value>\n" % fdef.value);
	if fdef.doc:
		os.write("<doc>%s</doc>\n" % fdef.doc);
	os.write("</field>\n");

    def marshal_message(self, mdef, os=sys.stdout):
	os.write("<message>\n");
	os.write("<msgType>%s</msgType>\n" % mdef.msgType);
	if mdef.doc:
		os.write("<doc>%s</doc>\n" % mdef.doc);
	for fieldDef in mdef.fieldDefs:
		self. marshal_field(fieldDef, os)
	if mdef.strict:
		os.write("<strict>%s</strict>\n" % mdef.strict);
	os.write("</message>\n");

    def marshal_interface(self, idef, os=sys.stdout):
	os.write("<interface>\n");
	os.write("<name>%s</name>\n" % idef.name);
	if idef.doc:
		os.write("<doc>%s</doc>\n" % idef.doc);
	if idef.inputMessageDefs:
		os.write("<inputMessage>\n");
		for mdef in idef.inputMessageDefs:
			self. marshal_message(mdef, os)
		os.write("</inputMessage>\n");
	if idef.outputMessageDefs:
		os.write("<outputMessage>\n");
		for mdef in idef.outputMessageDefs:
			self. marshal_message(mdef, os)
		os.write("</outputMessage>\n");
	os.write("</interface>\n");

    def marshal_client(self, cdef, os=sys.stdout):
	os.write("<client>\n");
	os.write("<name>%s</name>\n" % cdef.name);
	if cdef.doc:
		os.write("<doc>%s</doc>\n" % cdef.doc);
	if cdef.language:
		os.write("<language>%s</language>\n" % cdef.language);
	if cdef.source:
		os.write("<source>%s</source>\n" % cdef.source);
	if cdef.soucreControlProject:
		os.write("<sourceControlProject>%s</sourceControlProject>\n" % cdef.soucreControlProject);
	if cdef.interfaces:
		for idef in cdef.interfaces:
			self.marshal_interface(idef, os)
	
	os.write("</client>\n");

    def marshal(self, cdef, os=sys.stdout):
	os.write('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
	self.marshal_client(cdef, os)	


    """
    un-marshaller
    """
    def unmarshal_field(self, fieldNode):
	#print "unmarshal_field"
	fieldDefs = []
	name = None
	ftype = None
	optional = False
	default = None
	value = None
	doc = None
	for node in fieldNode.childNodes:
		if node.nodeType != node.ELEMENT_NODE:
			continue
		if node.nodeName == "name":
			name = node.firstChild.nodeValue
		if node.nodeName == "ftype":
			ftype = node.firstChild.nodeValue
		if node.nodeName == "optional":
			optional = node.firstChild.nodeValue
			if optional != None:
				optional = True
		if node.nodeName == "default":
			default = node.firstChild.nodeValue
		if node.nodeName == "value":
			value = node.firstChild.nodeValue
		if node.nodeName == "doc":
			doc = node.firstChild.nodeValue

	fd = 0
	if (name!= None and ftype != None):	
		fd = FieldDef(name, ftype, optional, default, value, doc)
	return fd

    def unmarshal_message(self, messageNode):
	#print "unmarshal_message"
	msgType = None
	doc = None
	fieldDefs = []
	strict = None
	for node in messageNode.childNodes:
		if node.nodeType != node.ELEMENT_NODE:
			continue
		
		if node.nodeName == "msgType":
			msgType = node.firstChild.nodeValue
		if node.nodeName == "doc":
			doc = node.firstChild.nodeValue
		if node.nodeName == "field":
			fieldDef = self.unmarshal_field(node)
			fieldDefs.append(fieldDef)
		if node.nodeName == "strict":
			strict = node.firstChild.nodeValue
	
	md = None
	if msgType != None:
		md = MessageDef(msgType, doc, fieldDefs, strict) 
	return md


    def unmarshal_messages(self, messagesNode):
	#print "unmarshal_messages"
	messageDefs = []
	
	for node in messagesNode.childNodes:
		if node.nodeType != node.ELEMENT_NODE:
			continue
		if node.nodeName == "message":
			messageDef = self.unmarshal_message(node)
			messageDefs.append(messageDef)
	
	return messageDefs

    def unmarshal_interface(self, interfaceNode):
	#print "unmarshal_interface"

	inputMessageDefs=None
	outputMessageDefs=None
	
	for node in interfaceNode.childNodes:
		if node.nodeType != node.ELEMENT_NODE:
			continue
		if node.nodeName == "name":
			name = node.firstChild.nodeValue
		if node.nodeName == "doc":
			doc = node.firstChild.nodeValue
		if node.nodeName == "inputMessage":
			inputMessageDefs = self.unmarshal_messages(node)
		if node.nodeName == "outputMessage":
			outputMessageDefs = self.unmarshal_messages(node)
	id = None
	if name != None:
		id = MessageInterfaceDef(name,doc,
					 inputMessageDefs,
					 outputMessageDefs)
	return id



    def unmarshal_client(self, clientNode):
	#print "unmarshal_clientNode"
	name = None
	doc = None
	language = None
	source = None
	sourceControlProject = None
	interfaces = []

	for node in clientNode.childNodes:
		if node.nodeType != node.ELEMENT_NODE:
			continue
		if node.nodeName == "name":
			name = node.firstChild.nodeValue
		if node.nodeName == "doc":
			doc = node.firstChild.nodeValue
		if node.nodeName == "language":
			language = node.firstChild.nodeValue
		if node.nodeName == "source":
			source = node.firstChild.nodeValue
		if node.nodeName == "sourceControlProject":
			sourceControlProject = node.firstChild.nodeValue
		if node.nodeName == "interface":
			interfaceDef = self.unmarshal_interface(node)
			interfaces.append(interfaceDef)

	cd = None
	if name != None:
		cd = ClientDef(name,doc,
				language,source,sourceControlProject,
				interfaces)
	return cd


    def unmarshal(self, buf):
	clientDef = None
        dom = xml.dom.minidom.parseString(buf)
	for node in dom.childNodes:
		if node.nodeType != node.ELEMENT_NODE:
			pass
		if node.nodeName == "client":
			clientDef = self.unmarshal_client(node)
		
	return clientDef

    def marshalToFile(self, cdef, path):
	ofile = open(path, "w")
	self.marshal(cdef,ofile)
	ofile.close()

    def unmarshalFromFile(self, path):
	str = open(path, "r").read()
	return self.unmarshal(str)

    def format(self, defn, opath=None):
        os = StringIO.StringIO()
	className = defn.__class__.__name__
	if className == ClientDef.__name__:
	    self.marshal_client(defn, os)
	elif className == MessageInterfaceDef.__name__:
            os.write(INTERFACE_HEADER % {'title': defn.name + " Interface"})
            self.marshal_interface(defn, os)
	else:
	    print "Cannot recognize object class:", className
	    sys.exit(1)
	os.seek(0)
	str = os.read()
	if opath:
	    os = open(opath, "w")
	    os.write(str)
	    os.close()
	return str


