
import sys, string
import DBObjectServer
db = DBObjectServer.MySQLInterface()
str = raw_input("This will delete any existing MDB database.  Are you sure?")
if not string.lower(str) in ['y', 'yes']:
   print "Aborting"
   sys.exit(1)
try:
   db.clearDatabase()
except:
   print "Cannot setup Database"
str = raw_input("Type any key to finish...")
