
import ObjectShare
ObjectShare.verbosity = 2

class DBObjectServer(ObjectShare.ObjectShareServer):
    def objIdToPath(self, objId):
	path = "C:/temp/obj_%s.txt" % objId
	return path

    def _setProps(self, obj, vals):
	ObjectShare.ObjectShareServer._setProps(self, obj, vals)
	print "****** Some Extra stuff needs to be done:", vals
	path = self.objIdToPath(obj.objectId)
	os = open(path, "w")
 	str = `obj.dict`
	print "*****:", str
	os.write("%s\n" % str)
	os.close()

    def initializeObject(self, obj):
	print "***** Could be initializing here...."
	path = self.objIdToPath(obj.objectId)
	try:
	   os = open(path, "r")
	   str = os.read()
	   print "Got Str: '%s'" % str
	   d = eval(str)
	   obj.dict = d
	except IOError:
	   pass
	except:
	   print "Unknown Error...."

	   
if __name__ == '__main__':
    s = DBObjectServer()
    ObjectShare.runObjectShareXMLRPCServer(s)
    s.run()
