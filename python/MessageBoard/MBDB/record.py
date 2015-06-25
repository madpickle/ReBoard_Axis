
import DB
mdb = DB.MessageBoardDB()
patterns = [
    {'msgType': 'kumo.*'},
    {'msgType': 'video.faceDetector*'},
    {'msgType': 'ePic*'},
    {'msgType': 'cin.setOwner'},
    {'msgType': 'cin.clearOwner'},
    {'msgType': 'cin.setView'},
    {'msgType': 'cin.viewRequest'}
]
mdb.recordMessages(patterns)

