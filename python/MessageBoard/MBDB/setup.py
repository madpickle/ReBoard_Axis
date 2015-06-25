
import sys, string
import DB
mdb = DB.MessageBoardDB()
str = raw_input("This will delete any existing MDB database.  Are you sure?")
if not string.lower(str) in ['y', 'yes']:
   print "Aborting"
   sys.exit(1)
try:
   mdb.clearDatabase()
except:
   print "Cannot setup Database"
str = raw_input("Type any key to finish...")
