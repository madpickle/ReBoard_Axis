import sys, traceback

if not "C:/FlyCam/FXPY" in sys.path:
    sys.path.append("C:/FlyCam/FXPY")
if not "C:/FlyCam/MessageBoard/python" in sys.path:
    sys.path.append("C:/FlyCam/MessageBoard/python")

import MBI

xmlPath = sys.argv[1]
htmlPath = sys.argv[2]

if xmlPath[-4:] == ".xml":
	import MBI_XmlFormatter
	f = MBI_XmlFormatter.Formatter()
	cd = f.unmarshalFromFile(xmlPath)
	cd.interfaces
	if htmlPath[-5:] == ".html":
		print cd.format(htmlPath)
	else:
		print "ERROR: illegal html file name"
else:
	print "ERROR: illegal xml file name"
