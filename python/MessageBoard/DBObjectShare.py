import sys, string, time
import MySQLdb

import ObjectShare
ObjectShare.verbosity = 0

VERBOSITY = 1
INCLUDE_SYSFIELDS = 1

CREATE_OBJECTS_TABLE = """
CREATE TABLE objects (
objectIdNum INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
objectId VARCHAR(50) NOT NULL,
INDEX(objectIdNum),
INDEX(objectId)
)
"""

CREATE_STATES_TABLE = """
CREATE TABLE states (
stateIdNum INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
objectIdNum INT NOT NULL,
MBTime DOUBLE NOT NULL,
INDEX(objectIdNum),
INDEX(stateIdNum)
)
"""

CREATE_PROPS_TABLE = """
CREATE TABLE props (
stateIdNum INT NOT NULL,
propName TEXT NOT NULL,
propValue TEXT NOT NULL,
INDEX(stateIdNum)
)
"""

class MySQLInterface:
    def __init__(self, host="localhost"):
	self.conn = MySQLdb.connect(db="objectshare", host=host,
				    user="root", passwd="flycam")
	self.createdTables = 0
        self.idx = 0
	cursor = self.conn.cursor()
	sql = "select count(objectid) FROM objects"
	try:
		cursor.execute(sql)
	except:
		print "No TABLE: objects"
		cursor.close()
		return	
	objectIdNum = cursor.fetchall()[0][0]
	objectIdNum = int(objectIdNum)
	if ObjectShare.verbosity > 1:
		print "objectIdNum:", objectIdNum
	
	sql = "select objectid FROM objects"
	cursor.execute(sql)

	n = 0
	self.objectIds = []
	while n < objectIdNum:
		objectId = cursor.fetchall()[n][0]	
		self.objectIds.append(objectId)
		if ObjectShare.verbosity > 1:
			print n, ":", objectId
		n += 1
	if ObjectShare.verbosity > 1:
		print self.objectIds
	cursor.close()


    def clearDatabase(self):
	self.removeTables()
	self.createTables()
	
    def removeTable(self, tableName):
	print "Removing "+tableName
        cursor = self.conn.cursor()
        try:
	    cursor.execute("DROP TABLE "+tableName)
	except:
	    print "Cannot delete Table "+tableName
	cursor.close()

    def removeTables(self):
	self.removeTable("objects")
	self.removeTable("states")
	self.removeTable("props")

    def createTables(self):
        cursor = self.conn.cursor()
	try:
	    print "Creating table OBJECTS"
   	    cursor.execute(CREATE_OBJECTS_TABLE)
	except:
	    print "Cannot create OBJECTS Table"
            cursor.close()
	    raise "SetupError"
	try:
	    print "Creating table STATES"
   	    cursor.execute(CREATE_STATES_TABLE)
	except:
	    print "Cannot create STATES Table"
            cursor.close()
	    raise "SetupError"
	try:
	    print "Creating PROPS"
   	    cursor.execute(CREATE_PROPS_TABLE)
	except:
	    print "Cannot create PROPS Table"
            cursor.close()
	    raise "SetupError"
        cursor.close()
	self.createdTables = 1

    def insertProps(self, stateIdNum, props, cursor):
	#print "ins prop", msg
	#
	# Now insert properties into props table
	#
	propStrs = []
	
	for key in props.keys():
		val = props[key]
		propStrs.append("%s" % ((stateIdNum, key, val),))
	if propStrs:
		vals = string.join(propStrs, ",")
		if ObjectShare.verbosity > 1:
			print vals
		insertQuery = "INSERT INTO PROPS VALUES " + vals
		cursor.execute(insertQuery)
    
    def insertState(self, objectIdNum, MBTime, props, cursor):
	
	# First insert into the States table
	tup = ('', objectIdNum, MBTime)
	if ObjectShare.verbosity > 1:
		print tup
	cursor.execute("INSERT INTO STATES VALUES %s " % (tup,))
	cursor.execute("SELECT LAST_INSERT_ID()")
	stateIdNum = cursor.fetchall()[0][0]
	stateIdNum  = int(stateIdNum)

	self.insertProps(stateIdNum, props, cursor)
	
    def insertObject(self, objectId, MBTime, props, cursor):
	if ObjectShare.verbosity > 1:
		print "ins Obj:", objectId
		
	if objectId in self.objectIds:
		sql =  "SELECT objectIdNum FROM objects WHERE objectId='" + objectId +"'"
		cursor.execute(sql)
		objectIdNum = cursor.fetchall()[0][0]
		objectIdNum = int(objectIdNum)
	else:
		# First insert into the objects table
		tup = ('', objectId)
		cursor.execute("INSERT INTO OBJECTS VALUES %s " % (tup,))
		cursor.execute("SELECT LAST_INSERT_ID()")
		objectIdNum = cursor.fetchall()[0][0]
		objectIdNum = int(objectIdNum)
		self.objectIds.append(objectId)

	self.insertState(objectIdNum, MBTime, props, cursor)

    def insert(self, objectId, MBTime, props):
        cursor = self.conn.cursor()
	print props
	self.insertObject(objectId, MBTime, props, cursor)	    
	cursor.close()



class DBObjectShareServer(ObjectShare.ObjectShareServer):
    def __init__(self, mbPortal=None, objPattern={}):
	ObjectShare.ObjectShareServer.__init__(self, mbPortal, objPattern)
	self.db = MySQLInterface()

    def storeState(self, obj, vals):
	ObjectShare.ObjectShareServer.storeState(self, obj, vals)
	if ObjectShare.verbosity > 1:
		print "****** Some Extra stuff needs to be done:", vals
	t = time.time()
	if ObjectShare.verbosity > 1:
		print "dbtime:", t
	self.db.insert(obj.objectId, t, obj.dict)

    def initializeObject(self, obj):
	if ObjectShare.verbosity > 1:
		print "***** Could be initializing here...."
	   
if __name__ == '__main__':
    s = DBObjectShareServer(objPattern={'objectId':'*'})
    ObjectShare.runObjectShareXMLRPCServer(s)
    s.run()
