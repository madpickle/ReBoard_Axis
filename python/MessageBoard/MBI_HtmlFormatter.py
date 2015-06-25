
from MBI import *
import sys, string, StringIO

HEADER = """
<html>
<head>
<title>%(title)s</title>
</head>
<body bgcolor="#CCCCDD">
<h2>%(title)s</h2>
Name: %(name)s<br>\n
Language: %(language)s<br>\n
Description:
<ul>
%(doc)s
</ul>
"""

INTERFACE_HEADER = """
<html>
<head>
<title>%(title)s</title>
</head>
<body>
"""

FOOTER = """
</body>
</html>
"""

TABLE_HEADER = """
<tr>
<th>Field Name</th>
<th>Type</th>
<th></th>
<!--
<th>Value</th>
-->
<th width="20">  </th>
<th>Comment</th>
</tr>
"""

"""
def getName(obj):
    if type(obj) == type("string"):
	return obj
    return obj.name
"""

class Formatter:
    def outputFieldDefRow(self, os, name, ftype, opt, value, doc):
	os.write(' <tr valign="top">\n')
	os.write("  <td>%s</td>\n" % name)
	os.write("  <td>%s</td>\n" % ftype)
	os.write("  <td>%s</td>\n" % opt)
#	os.write("  <td>%s</td>\n" % value)
	os.write("  <td>%s</td>\n" % "  ")
	os.write("  <td>%s</td>\n" % doc)
	os.write(" </tr>\n")

    def formatFieldDef(self, fdef, os=sys.stdout):
	opt = ""
	if fdef.optional:
	   opt = "Optional "
        doc = ""
	if fdef.doc:
	   doc = "	%s" % fdef.doc
	val = ""
	if fdef.value:
	    val = fdef.value
	self.outputFieldDefRow(os, fdef.name, fdef.ftype, opt, val, doc)

    def formatMessageDef(self, mdef, os=sys.stdout):
	replyStr = ""
	if mdef.replyMessageType:
	   replyStr = "&nbsp;&nbsp;&nbsp;returns: %s" % mdef.replyMessageType
        os.write("<h3>%s%s</h3>\n" % (mdef.msgType, replyStr))
	if mdef.doc:
	    os.write("<p>\n")
            os.write(mdef.doc)
	    os.write("<p>")
	if mdef.fieldDefs:
	   os.write("<table>\n")
	   os.write(TABLE_HEADER)
#	   self.outputFieldDefRow(os, "msgType", String, "", mdef.msgType, "Message Type")
           for fieldDef in mdef.fieldDefs:
	      self.formatFieldDef(fieldDef, os)
	   os.write("</table>\n")
        os.write("<hr align='left' width='200'>\n")

    def formatInterfaceDef(self, idef, os=sys.stdout):
        os.write("<p><h2>Message Interface: %s</h2>\n" % idef.name)
        os.write("<p><h3>Description:</h3>\n")
	os.write("<ul>\n")
	os.write("%s\n" % idef.doc)
	os.write("</ul>\n")
        if idef.inputMessageDefs:
            os.write("<h3>Input Message Defs:</h3>\n")
	    os.write("<ul>\n")
            for mdef in idef.inputMessageDefs:
                self.formatMessageDef(mdef, os)
                os.write("\n")
                #os.write('<hr width="100">\n')
	    os.write("</ul>\n")
        if idef.outputMessageDefs:
            os.write("<h3>Output Message Defs:</h3>\n")
	    os.write("<ul>\n")
            for mdef in idef.outputMessageDefs:
                self.formatMessageDef(mdef, os)
                os.write("\n")
                #os.write('<hr width="100">\n')
	    os.write("</ul>\n")

    def formatClientDef(self, clientDef, os=sys.stdout, showInterfaceDefs=1):
	os.write(HEADER % {
	   'title': clientDef.name + " Client",
	   'name': clientDef.name,
	   'language': clientDef.language,
	   'doc': clientDef.doc
         })
	if clientDef.interfaces:
	    os.write("<h3>Message Interfaces Implemented:</h3>\n")
	    os.write("<ul>\n")
	    for idef in clientDef.interfaces:
		os.write("<li>%s\n" % getName(idef))
	    os.write("</ul>\n")
	if clientDef.interfacesUsed:
	    os.write("<h3>Message Interfaces Used:</h3>\n")
	    os.write("<ul>\n")
	    for idef in clientDef.interfacesUsed:
	        name = getName(idef)
		os.write("<li>%s\n" % name)
	    os.write("</ul>\n")

	if showInterfaceDefs and clientDef.interfaces:
	    for idef in clientDef.interfaces:
	        try:
	           idef = getInterfaceDef(idef)
	           os.write("<hr>\n")
	           self.formatInterfaceDef(idef, os)
	        except:
	           pass

    def format(self, defn, opath=None):
        os = StringIO.StringIO()
	className = defn.__class__.__name__
	if className == ClientDef.__name__:
	    self.formatClientDef(defn, os)
	elif className == MessageInterfaceDef.__name__:
            os.write(INTERFACE_HEADER % {'title': defn.name + " Interface"})
            self.formatInterfaceDef(defn, os)
	else:
	    print "Cannot recognize object class:", className
	    sys.exit(1)
        os.write(FOOTER)
	os.seek(0)
	str = os.read()
	if opath:
	    os = open(opath, "w")
	    os.write(str)
	    os.close()
	return str


