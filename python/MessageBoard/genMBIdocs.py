import os, sys, string, traceback

"""
if not "C:/FlyCam/FXPY" in sys.path:
    sys.path.append("C:/FlyCam/FXPY")
if not "C:/FlyCam/MessageBoard/python" in sys.path:
    sys.path.append("C:/FlyCam/MessageBoard/python")
"""

import MBI

HEADER = """<html>
<head>
</head>
<body bgcolor="#CCCCDD">
<h1>MessageBoard Client and Interface Directory</h1>
"""

FOOTER = """
</body>
</html>
"""

def strCmp(s1, s2):
    return cmp(string.lower(s1), string.lower(s2))

def getName(obj):
    if type(obj) == type("string"):
	return obj
    return obj.name

def authorsStr(authors):
    if type(authors) == type("string"):
	return authors
    return string.join(authors, ", ")

def linkStr(name, url):
    return '<a href="%s">%s</a>' % (url, name)

def format(names, htmlDir="html", xmlDir="xml"):
    verbosity = 2
    if htmlDir:
        try:
            print "Creating", htmlDir
            os.mkdir(htmlDir)
        except:
            pass
    if xmlDir:
        try:
            print "Creating", xmlDir
            os.mkdir(xmlDir)
        except:
            pass
    #
    # First import all necessary interface modules
    #
    for name in names:
	print "Importing %s_mbi.py" % name
        com = "import %s_mbi" % name
        exec(com)

    #
    # Now generate the necessary Client and Interface HTML pages
    #
    for defn in MBI.CLIENT_DEFS.values():
	path = "%s.client.html" % defn.name
        if htmlDir:
            path = os.path.join(htmlDir,path)
        print "Creating", path
        defn.format(path)

    for defn in MBI.INTERFACE_DEFS.values():
	path = "%s.interface.html" % defn.name
        if htmlDir:
            path = os.path.join(htmlDir,path)
        print "Creating", path
        defn.format(path)

    #
    # Output XML definations
    #
    for defn in MBI.CLIENT_DEFS.values():
	path = "%s.client.xml" % defn.name
        print "Creating", path
        if xmlDir:
            path = os.path.join(xmlDir,path)
	try:
           defn.format(path)
	except:
	   print "Exception in saving XML for", defn.name

    #
    # Generate top level index file
    #
    clientNames = MBI.CLIENT_DEFS.keys()
    clientNames.sort(strCmp)
    interfaceNames = MBI.INTERFACE_DEFS.keys()
    interfaceNames.sort(strCmp)
    opath = "index.html"
    if htmlDir:
        opath = os.path.join(htmlDir, opath)
    print "Creating", path
    ofile = open(opath, 'w')
    ofile.write(HEADER)
    ofile.write("<h2>Registered Clients</h2>")
    ofile.write("<ul>")
    for name in clientNames:
        link = linkStr(name, "%s.client.html" % name)
	if verbosity > 1:
	    ofile.write("<p>\n")
	    clientDef = MBI.CLIENT_DEFS[name]
	    ofile.write("<b>%s</b><br>\n" % link)
	    if clientDef.authors:
	       ofile.write("Authors: %s<br>\n" % authorsStr(clientDef.authors))
	    if clientDef.language:
	       ofile.write("Language: %s<br>\n" % clientDef.language)
	    if clientDef.interfacesUsed:
	        ofile.write("Interfaces Used: ")
	        for idef in clientDef.interfacesUsed:
	            name = getName(idef)
                    link = linkStr(name, "%s.interface.html" % name)
	            ofile.write("%s " % link)
	        ofile.write("<br>\n")
	    if clientDef.interfaces:
	        ofile.write("Interfaces Implemented: ")
	        for idef in clientDef.interfaces:
	            name = getName(idef)
                    link = linkStr(name, "%s.interface.html" % name)
	            ofile.write("%s " % link)
	        ofile.write("<br>\n")
            ofile.write("Description:<br>\n")
            ofile.write("<ul>\n%s\n</ul>\n" % clientDef.doc)
	    ofile.write("<p>\n")
	    ofile.write("%s\n" % str)
	else:
	    ofile.write("<li>%s\n" % link)
    ofile.write("</ul>")
    ofile.write("<h2>Registered Interfaces</h2>")
    ofile.write("<ul>")
    for name in interfaceNames:
        link = linkStr(name, "%s.interface.html" % name)
	ofile.write("<li>%s\n" % link)
    ofile.write("</ul>")
    ofile.write(FOOTER)
    ofile.close()

def formatDir(dir):
    suffix = "_mbi.py"
    suflen = len(suffix)
    names = []
    fnames = os.listdir(dir)
    for fname in fnames:
	if fname[-suflen:] == suffix:
	    names.append(fname[:-suflen])
    format(names)

def run():
    try:
        formatDir(".")
    except:
        traceback.print_exc()
        input("Type <enter> to exit")

if __name__ == '__main__':
    run()

