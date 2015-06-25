
import os
import ObjectShare
ObjectShare.verbosity = 2

#STORAGE_DIR = "C:/temp"
STORAGE_DIR = "ObjectStorageDir"

    
class FSObjectServer(ObjectShare.ObjectShareServer):
    def __init__(self, mbPortal=None, objPattern={}):
        if not os.path.exists(STORAGE_DIR):
            print "Creating Directory", STORAGE_DIR
            os.mkdir(STORAGE_DIR)
        ObjectShare.ObjectShareServer.__init__(self, mbPortal, objPattern)
        
    def objIdToPath(self, objId):
#	path = "C:/temp/obj_%s.txt" % objId
	path = os.path.join(STORAGE_DIR, "obj_%s.txt" % objId)
	return path

    def storeState(self, obj, vals):
	ObjectShare.ObjectShareServer.storeState(self, obj, vals)
	#print "****** Some Extra stuff needs to be done:", vals
	path = self.objIdToPath(obj.objectId)
	os = open(path, "w")
 	str = `obj.dict`
	os.write("%s\n" % str)
	os.close()

    def initializeObject(self, obj):
	print "Initializing object...."
	path = self.objIdToPath(obj.objectId)
	print "reading from path:", path
	try:
	   os = open(path, "r")
	   str = os.read()
	   #print "Got Str: '%s'" % str
	   d = eval(str)
	   obj.dict = d
           print "Got dictionary:", d
	except IOError:
	   pass
	except:
	   print "Unknown Error...."

	   
if __name__ == '__main__':
    s = FSObjectServer(objPattern={'objectId':'*'})
    ObjectShare.runObjectShareXMLRPCServer(s)
    s.run()
