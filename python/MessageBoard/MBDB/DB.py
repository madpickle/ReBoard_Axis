
import sys, string, time
import MySQLdb

sys.path.append("../")
import MessageBoard

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

CREATE_MESSAGES_TABLE = """
CREATE TABLE messages (
msgId INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
msgType VARCHAR(50) NOT NULL,
msgTime DOUBLE NOT NULL,
objectIdNum INT NOT NULL,
INDEX(msgId),
INDEX(msgType),
INDEX(msgTime),
INDEX(objectIdNum)
)
"""

CREATE_PROPS_TABLE = """
CREATE TABLE props (
msgId INT NOT NULL,
propName TEXT NOT NULL,
propValue TEXT NOT NULL,
INDEX(msgId)
)
"""


class MBDB_Handler(MessageBoard.SimpleMessageHandler):
    def __init__(self, mdb):
	MessageBoard.SimpleMessageHandler.__init__(self)
	self.mdb = mdb

    def handleMessage(self, msg):
	if VERBOSITY:
	    print msg
	self.mdb.insert(msg)

class MessageBoardDB:
    def __init__(self, host="localhost"):
	self.conn = MySQLdb.connect(db="test", host=host,
				    user="root", passwd="flycam")
	self.createdTables = 0
        self.idx = 0

    def recordMessages(self, patterns=None):
	if not self.createdTables:
   	    try:
	       self.createTables()
	    except:
	       pass
	self.client = MessageBoard.MessageClient()
	self.handler = MBDB_Handler(self)
	if patterns == None:
	    print "Registering to insert all messages"
	    self.client.registerMessageHandler(self.handler)
	else:
	    for pattern in patterns:
	        print "Registering to insert messages matching", pattern
	        self.client.registerMessageHandler(self.handler, pattern)
	self.client.listenForever()

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
	self.removeTable("messages")
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
	    print "Creating table MESSAGES"
   	    cursor.execute(CREATE_MESSAGES_TABLE)
	except:
	    print "Cannot create MESSAGES Table"
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

    def insertProps(self, msgId, msg, cursor):
	#print "ins prop", msg
	#
	# Now insert properties into props table
	#
	propStrs = []
	for key in msg.keys():
		val = msg[key]
		propStrs.append("%s" % ((msgId, key, val),))
	if propStrs:
		vals = string.join(propStrs, ",")
		insertQuery = "INSERT INTO PROPS VALUES " + vals
		#print "Prop Insert Query:", insertQuery
 	        cursor.execute(insertQuery)
    
    def insertMessages(self, objectIdNum, msg, cursor):
	#print "ins msg", msg
	t = time.time()

	# First insert into the Messages table
	msgType = msg['msgType']
	tup = ('', msgType, t, objectIdNum)
	cursor.execute("INSERT INTO MESSAGES VALUES %s " % (tup,))
	cursor.execute("SELECT LAST_INSERT_ID()")
	msgId = cursor.fetchall()[0][0]
	msgId = int(msgId)

	del msg['msgType']
	self.insertProps(msgId, msg, cursor)
	
    def insertObjects(self, msg, cursor):
	print "ins Obj", msg
	
	objectId = msg['objectID']
	sql = "SELECT COUNT(*) FROM objects WHERE objectId='" + objectId +"'"
	cursor.execute(sql)
	num = cursor.fetchall()[0][0]
	num = int(num)
		
	if(num == 0):
		# First insert into the objects table
		tup = ('', objectId)
		cursor.execute("INSERT INTO OBJECTS VALUES %s " % (tup,))
		cursor.execute("SELECT LAST_INSERT_ID()")
		objectIdNum = cursor.fetchall()[0][0]
		objectIdNum = int(objectIdNum)
	else:
		sql =  "SELECT objectIdNum FROM objects WHERE objectId='" + objectId +"'"
		cursor.execute(sql)
		objectIdNum = cursor.fetchall()[0][0]
		objectIdNum = int(objectIdNum)

	del msg['objectID']
	self.insertMessages(objectIdNum, msg, cursor)

    def insert(self, msg):
        cursor = self.conn.cursor()
	self.insertObjects(msg, cursor)	    
	cursor.close()

    def deleteMsgId(self, msgId):
	cursor = self.conn.cursor()
	try:
	    QUERY = "DELETE FROM messages WHERE msgId = '%s'" % msgId
	    #print QUERY
	    cursor.execute(QUERY)
	    QUERY = "DELETE FROM props WHERE msgId = '%s'" % msgId
	    #print QUERY
	    cursor.execute(QUERY)
	finally:
	    cursor.close()

    def deleteMessages(self, msgType, maxNum=20):
	cursor = self.conn.cursor()
	cursor.execute("SELECT msgId, msgType, msgTime FROM messages WHERE msgType='%s' LIMIT %s" % (msgType, maxNum))
        tups = cursor.fetchall()
	try:
	    for tup in tups:
	        msgId, msgType, msgTime = tup
                print msgId, msgType, msgTime
	        self.deleteMsgId(msgId)
	        QUERY = "DELETE FROM messages WHERE msgId = '%s'" % msgId
	        #print QUERY
	        cursor.execute(QUERY)
	        QUERY = "DELETE FROM props WHERE msgId = '%s'" % msgId
	        #print QUERY
	        cursor.execute(QUERY)
	finally:
	    cursor.close()


    def delete(self, msgType=None, startTime=None, endTime=None):
#	DELETE_QUERY = "DELETE QUICK FROM messages, props USING messages, props "
	DELETE_QUERY = "DELETE QUICK messages, props FROM messages, props "
	patObj = None
	predStrs = ["messages.msgId = props.msgId"]
	if startTime != None:
	    predStrs.append("messages.msgTime >= %f" % startTime)
	if endTime != None:
	    predStrs.append("messages.msgTime <= %f" % endTime)
	if msgType:
	    if msgType[-1:] == '*':
	        predStrs.append("messages.msgType LIKE %s" % `msgType[:-1]+'%'`)
	    else:
	     	predStrs.append("messages.msgType=%s" % `msgType`)
	if predStrs:
	    predStr = string.join(predStrs, " AND ")
	    DELETE_QUERY += " WHERE " + predStr
	print "Query:", DELETE_QUERY
	cursor = self.conn.cursor()
	try:
	    print "locking..."
	    cursor.execute("LOCK TABLES messages WRITE, props WRITE")
	    print "Got lock"
	    cursor.execute(DELETE_QUERY)
	    result = cursor.fetchall()
	    print result
	finally:
	    print "unlocking..."
	    cursor.execute("UNLOCK TABLES")
	    print "unlocked"
	    cursor.close()
	return result

    def fetch(self, pattern=None, startTime=None, endTime=None):
	MSG_QUERY = "SELECT msgId, msgType, msgTime FROM MESSAGES"
	PROPS_QUERY = "SELECT propName, propValue FROM PROPS"
	patObj = None
	predStrs = []
	if startTime != None:
	    predStrs.append("msgTime >= %f" % startTime)
	if endTime != None:
	    predStrs.append("msgTime <= %f" % endTime)
	if type(pattern) == type({}):
	    patObj = MessageBoard.Pattern(pattern)
	    if pattern.has_key('msgType'):
	        msgType = pattern['msgType']
	        if msgType[-1:] == '*':
	            predStrs.append("msgType LIKE %s" % `msgType[:-1]+'%'`)
		else:
	            predStrs.append("msgType=%s" % `msgType`)
	if predStrs:
	    predStr = string.join(predStrs, " AND ")
	    MSG_QUERY += " WHERE " + predStr
	msgs = []
	print "Query:", MSG_QUERY
	cursor = self.conn.cursor()
	try:
	    cursor.execute(MSG_QUERY)
	    tups = cursor.fetchall()
	    #print "Tups:", tups
	    for tup in tups:
	        id, msgType, t = tup
	        msg = {'msgType':msgType, 'msgTime':t}
	        if INCLUDE_SYSFIELDS:
	            msg['system.msgId'] = id
	        try:
		    cursor2 = self.conn.cursor()
	            cursor2.execute(PROPS_QUERY + ' WHERE msgId="%s"' % id)
	            for ptup in cursor2.fetchall():
			propName, propVal = ptup
	                msg[propName] = propVal
		finally:
	            cursor2.close()
		if patObj == None or patObj.matches(msg):
	            msgs.append(msg)
	finally:
	    cursor.close()
	return msgs

    def getLastTime(self, msgType=None, endTime=None):
	MSG_QUERY = "SELECT MAX(msgTime) FROM MESSAGES"
	patObj = None
	predStrs = []
	if endTime != None:
	    predStrs.append("msgTime <= %f" % endTime)
	if msgType:
	    if msgType[-1:] == '*':
	        predStrs.append("msgType LIKE %s" % `msgType[:-1]+'%'`)
	    else:
	     	predStrs.append("msgType=%s" % `msgType`)
	if predStrs:
	    predStr = string.join(predStrs, " AND ")
	    MSG_QUERY += " WHERE " + predStr
	msgs = []
	print "Query:", MSG_QUERY
	cursor = self.conn.cursor()
	lastTime = None
	try:
	    cursor.execute(MSG_QUERY)
	    tups = cursor.fetchall()
	    lastTime = tups[0][0]
	finally:
	    cursor.close()
	return lastTime

    def fetchLast(self, msgType, endTime=None):
	t = self.getLastTime(msgType, endTime)
	if t == None:
	    return []
	return self.fetch({'msgType':msgType}, t, t)

    def dump(self, pattern=None, startTime=None, endTime=None, out=sys.stdout):
	msgs = self.fetch(pattern, startTime, endTime)
	out.write("Num Messages: %d\n" % len(msgs))
	for msg in msgs:
	    out.write("%s\n" % msg)
	out.write("Num Messages: %d\n" % len(msgs))

    def counts(self, msgType=None, startTime=None, endTime=None, out=sys.stdout):
	MSG_QUERY = "SELECT msgType, COUNT(msgId)" + \
                       "FROM MESSAGES GROUP BY msgType"
	patObj = None
	predStrs = []
	if startTime != None:
	    predStrs.append("msgTime >= %s" % startTime)
	if endTime != None:
	    predStrs.append("msgTime <= %s" % endTime)
	if msgType != None:
	    if msgType[-1:] == '*':
	        predStrs.append("msgType LIKE %s" % `msgType[:-1]+'%'`)
	    else:
	        predStrs.append("msgType=%s" % `msgType`)
	if predStrs:
	    predStr = string.join(predStrs, " AND ")
	    MSG_QUERY += " WHERE " + predStr
	print "Query:", MSG_QUERY
	cursor = self.conn.cursor()
	try:
	    cursor.execute(MSG_QUERY)
	    tups = cursor.fetchall()
	    for tup in tups:
	        msgType, count = tup
		out.write("%20s  %10d\n" % (msgType, count))
	finally:
	    cursor.close()

    def stats(self, msgType=None, startTime=None, endTime=None, out=sys.stdout):
	MSG_QUERY = "SELECT msgType, COUNT(msgId), MIN(msgTime), MAX(msgTime)" + \
                       "FROM MESSAGES GROUP BY msgType"
	patObj = None
	predStrs = []
	if startTime != None:
	    predStrs.append("msgTime >= %s" % startTime)
	if endTime != None:
	    predStrs.append("msgTime <= %s" % endTime)
	if msgType != None:
	    if msgType[-1:] == '*':
	        predStrs.append("msgType LIKE %s" % `msgType[:-1]+'%'`)
	    else:
	        predStrs.append("msgType=%s" % `msgType`)
	if predStrs:
	    predStr = string.join(predStrs, " AND ")
	    MSG_QUERY += " WHERE " + predStr
	print "Query:", MSG_QUERY
	cursor = self.conn.cursor()
	try:
	    cursor.execute(MSG_QUERY)
	    tups = cursor.fetchall()
	    for tup in tups:
	        msgType, count, minTime, maxTime = tup
		out.write("%20s  %10d  %s  %s\n" % \
                        (msgType, count, time.ctime(minTime), time.ctime(maxTime)))
	finally:
	    cursor.close()


def record():
    mdb = MessageBoardDB()
    try:
        mdb.clearDatabase()
    except:
	print "Cannot setup Database"
	sys.exit(1)
    patterns = [
        {'msgType': 'sound.direction'},
        {'msgType': 'kumo.*'},
        {'msgType': 'video.faceDetector*'},
        {'msgType': 'cin.*'}
    ]
    mdb.recordMessages(patterns)

if __name__ == '__main__':
    record()
