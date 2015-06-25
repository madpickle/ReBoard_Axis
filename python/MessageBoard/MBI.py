"""
This module contains definitions used for specifying message interfaces
"""

CLIENT_DEFS = {}
INTERFACE_DEFS = {}

PYTHON = "python"
CPP = "C++"
JAVA = "Java"
JAVASCRIPT = "JavaScript"
HTML = "HTML"
HTTP = "HTTP"


Any =           "Any"
String =	"String"
Int = 		"Integer"
Integer =	"Integer"
Float = 	"Float"
Time = 		"Time"
Bool =		"Bool"
StringVec = 	"StringVec"
IntVec = 	"IntVec"
FloatVec = 	"FloatVec"
FloatVec2 = 	"FloatVec2"
FloatVec3 = 	"FloatVec3"
FloatVec4 = 	"FloatVec4"
FloatVecVec = 	"FloatVecVec"
IntVecVec = 	"IntVecVec"



ftypes = [
   String,
   Int,
   Float,
   Bool,
   StringVec,
   IntVec,
   FloatVec,
   IntVecVec,
   FloatVecVec
]

class FieldDef:
    def __init__(self, name, ftype, optional=False, default=None, value=None, doc=None):
        self.name = name
        self.ftype = ftype
        self.optional = optional
        self.default = default
	self.value = value
        self.doc = doc

class MessageDef:
    def __init__(self, msgType, doc=None, fieldDefs=[], strict=False, replyMessageType=None):
        self.msgType = msgType
        self.doc = doc
        self.fieldDefs = fieldDefs
	self.replyMessageType = replyMessageType
        self.strict = strict            # Specifies whether additional ad hoc fields
                                        # should be allowed.

class MessageInterfaceDef:
    def __init__(self,
                 name,
                 doc,
	         authors = None,
                 inputMessageDefs=None,
                 outputMessageDefs=None):
        self.name = name
        self.doc = doc
        self.inputMessageDefs = inputMessageDefs
        self.outputMessageDefs = outputMessageDefs
        self.authors = authors
	INTERFACE_DEFS[name] = self

    def format(self, path=None):
	return format(self, path)

class ClientDef:
    def __init__(self,
                 name,
                 doc,
                 language=None,
                 source=None,
	         authors = None,
                 sourceControlProject=None,
	         interfaces=[],
	         interfacesUsed=[]):
        self.name = name
        self.doc = doc
        self.language = language
        self.source = source
        self.soucreControlProject = sourceControlProject
        self.interfaces = interfaces
        self.interfacesUsed = interfacesUsed
        self.authors = authors
	CLIENT_DEFS[name] = self

    def format(self, path=None):
	return format(self, path)


#
# Convenience functions...
#
def getName(obj):
    if type(obj) == type("String"):
	return obj
    return obj.name

def getClientDef(obj):
    if type(obj) == type("String"):
        obj = CLIENT_DEFS[obj]
    return obj

def getInterfaceDef(obj):
    if type(obj) == type("String"):
        obj = INTERFACE_DEFS[obj]
    return obj
    
def format(obj, path=None):
    if path == None:
	path = obj.name + ".html"
    if path[-5:] == ".html":
        import MBI_HtmlFormatter
	f = MBI_HtmlFormatter.Formatter()
    elif path[-4:] == ".xml":
	import MBI_XmlFormatter
	f = MBI_XmlFormatter.Formatter()
    else:
        import MBI_Formatter
        f = MBI_Formatter.Formatter()
    return f.format(obj, path)



if __name__ == '__main__':
    cd = ClientDef(name="dummyClient1",
                   doc="This is a bogus client that doesn't really exist.",
                   language=PYTHON,
		   interfaces = [
		       MessageInterfaceDef(name="dummy interface",
                                    doc="simple dummy interface",
                                    inputMessageDefs = [
                                    ],
                                    outputMessageDefs = [
                                       MessageDef(msgType="cin.status")
                                    ])])
    print cd.format("foo.html")






