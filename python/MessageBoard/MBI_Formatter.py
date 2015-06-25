
from MBI import *
import sys, string, StringIO

class Formatter:
    def writeLines(self, str, os, indent=3):
        istr = " "*indent
	parts = string.split(str, "\n")
	parts = map(lambda s: istr+s, parts)
	str = string.join(parts, "\n")
	os.write(str)

    def formatFieldDef(self, fdef, os=sys.stdout, indent=3):
        istr = " "*indent
	opt = ""
	if fdef.optional:
	   opt = "Optional "
        doc = ""
	if fdef.doc:
	   doc = "	%s" % fdef.doc
	str = "%s%s: %s%s" % (istr, fdef.name, opt, fdef.ftype)
        os.write("%-30s %s\n" % (str, doc))

    def formatMessageDef(self, mdef, os=sys.stdout, indent=3):
        istr = " "*indent
        os.write("%smsgType: %s\n" % (istr, mdef.msgType))
        for fieldDef in mdef.fieldDefs:
	    self.formatFieldDef(fieldDef, os, indent)
	if mdef.doc:
	    os.write("\n")
            self.writeLines(mdef.doc, os)
	    os.write("\n")

    def formatInterfaceDef(self, idef, os=sys.stdout, indent=3):
        os.write("Name: %s\n" % idef.name)
        os.write("Interfaces:\n%s\n\n" % idef.doc)
        if idef.inputMessageDefs:
            os.write("Input Message Defs:\n\n")
            for mdef in idef.inputMessageDefs:
                self.formatMessageDef(mdef, os)
                os.write("\n")
                os.write("   ----------------\n")
        if idef.outputMessageDefs:
            os.write("Output Message Defs:\n\n")
            for mdef in idef.outputMessageDefs:
                self.formatMessageDef(mdef, os)
                os.write("\n")
                os.write("   ----------------\n")

    def formatClientDef(self, clientDef, os=sys.stdout, indent=3):
        os.write("Name: %s\n" % clientDef.name)
        os.write("Language: %s\n" % clientDef.language)
        os.write("Description:\n%s\n\n" % clientDef.doc)
	if clientDef.interfaces:
	    os.write("Interfaces:\n\n")
	for idef in clientDef.interfaces:
	    self.formatInterfaceDef(idef, os, indent+3)

    def format(self, clientDef, path=None):
        os = StringIO.StringIO()
	self.formatClientDef(clientDef, os)
	os.seek(0)
	return os.read()


