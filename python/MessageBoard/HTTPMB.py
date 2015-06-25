
from MessageBoard import *
import MessageBoard
import SocketServer
import socket
import ReportGen
import cgi
import json
import os
from JSONMarshaller import JSONMarshaller

PARANOID = 0
BANNER_PAGE = None
ALLOW_QSTR_ON_SIMPLE_REQUESTS = True

HANDLER_CLASS = None

if os.path.exists("index.html"):
    BANNER_PAGE = "index.html"

###################################################################################
#
# HTTPMessageServer classes
#
import BaseHTTPServer
import SimpleHTTPServer
import traceback

class URLMarshaller:
    type = "URL"

    def marshal(self, obj):
        dict = obj
	str = ""
	for key in dict.keys():
	    str = str + ("%s=%s&" % (`key`, `dict[key]`))
	str = str[:-1]
        return str

    def unmarshal_(self, buf):
        dict = {}
	if buf == "":
	    return dict
        parts = string.split(buf, "&")
        for part in parts:
            pair = string.split(part, "=")
            if len(pair) != 2:
                print "Bad qspec:", buf
                raise ValueError
            key = pair[0]
            value = pair[1]
            dict[key] = urllib.unquote(value)
        return dict

    def unmarshal(self, buf):
        try:
            return self.unmarshal_(buf)
        except:
            raise ValueError

errorHtmlStr = """
<html>
<h3>Unrecognized Request: %s</h3>
<p>
<b><a href="/help">Help</a></b>
</html>
"""

cautiousHtmlStr = """
<html>
<h3>HTTP Server Retired</h3>
</html>
"""

helpHtmlStr = """
<html>
<h3>MessageBoard URL's:</h3>
<table>
<tr><td>
<a href="/status">/status</a>
</td>
<td>
Show status information about this MessageBoard
</td></tr>
<tr><td>
<a href="/getServerInfo">/getServerInfo</a>
</td>
<td>
Some of the same information as from /status in JSON form.
</td></tr>
<tr><td>
<a href="/getLatestMessages">/getLatestMessages[?msgType=<i>type</i>]</a>
</td>
<td>
The most recent messages by type.
</td></tr>
<tr><td>
<a href="/help">/help</a>
</td>
<td>
Show this help information.
</td></tr>
<tr><td>
<a href="/watchMessages">/watchMessages</a>
<td>
Print all messages to this browser...
</td></tr>
<tr><td>
/watchMessages?field1=val1&field2=val2...
<td>
Watch all messages that match the given values.
</td></tr>
<tr><td>
<a href="/sendMessage?msgType=test.ping">/sendMessage?msgType=test.ping</a>
<td>
Send a test message of type "test.ping".
</td></tr>
<tr><td>
/sendMessage?field1=val1&field2=val2...
<td>
Send a message with the specified field values.
</td></tr>
</table>
</html>
"""

def getServerInfo(server):
    import json
    hub = server.hub
    dict = {}
    lastMessages = []
    keys =  hub.lastMessageByType.keys()
    keys.sort()
    for key in keys:
        msg = {'message': hub.lastMessageByType[key],
               'client': hub.lastPeerByType[key],
               'time': hub.lastTimeByType[key]}
        lastMessages.append(msg)
    dict['lastMessages'] = lastMessages
    return json.dumps(dict, sort_keys=True, indent=4)

def getLatestMessages(server, queryDict):
    import json
    hub = server.hub
    if hub.messageCache != None:
        print "Using message cache"
        records = hub.messageCache.getLatestMessageRecords(Pattern(queryDict))
        return json.dumps(records, sort_keys=True, indent=4)
    pattern = Pattern(queryDict)
    dict = {}
    lastMessages = []
    keys =  hub.lastMessageByType.keys()
    keys.sort()
    for key in keys:
        msg = hub.lastMessageByType[key]
        if not pattern.matches(msg):
            continue
        record = {'message': hub.lastMessageByType[key],
                  'client': hub.lastPeerByType[key],
                  'time': hub.lastTimeByType[key]}
        lastMessages.append(record)
    return json.dumps(lastMessages, sort_keys=True, indent=4)


class HTTPMessageRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler, PeerHandler):
    def __init__(self, request, client_address, server):
	host, port = client_address
	hostname = socket.getfqdn(host)
	clientAddress = "%s %s" % (hostname, `client_address`)
	self.marshaller = Marshaller()
	self.clientAddressStr = clientAddress
	PeerHandler.__init__(self, "HTTP", server.hub, clientAddress)
	SimpleHTTPServer.SimpleHTTPRequestHandler.__init__(self,
				 request, client_address, server)

    def address_string(self):
        host, port = self.client_address[:2]
	if self.server.lookupHostnames:
            return socket.getfqdn(host)
	else:
	    return "%s : %d" % (host, port)

    def sendHeaders(self, mtype):
        self.send_response(200)
        self.send_header("Content-type", mtype)
        self.send_header("Cache-Control", "private")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Cache-Control", "must-revalidate")
        self.send_header("Cache-Control", "max-age=0")
        self.send_header("Pragma:", "no-cache")
        self.end_headers()

    def do_POST(self):
	#print "Doing POST"
	path = self.path
	#print "path:", self.path
	if path == "/postMessage":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
  	    self.wfile.write("Got POST %s\n" % self.path)
# 	    msgbuf = self.rfile.readline()
 	    msgbuf = self.rfile.read()
	    msgbuf = string.strip(msgbuf)
	    msg = cgi.parse_qs(msgbuf, 1)
	    for key in msg.keys():
	        msg[key] = msg[key][0]
	    print "Msg buf:", msgbuf
            print "Msg:", msg
            self.server.hub.handleMessage(self, msg, msgbuf, "url-encoded")
	    self.wfile.write("String:\n%s\n" % msgbuf)
            self.wfile.write("Dict:\n%s\n" % msg)
	    return
	if path == "/postMessages":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            length = int(self.headers.getheader('Content-Length'))
            ctype,pdict = cgi.parse_header(self.headers.getheader('Content-type'))
            data = {}
            if ctype == 'multipart/form-data':
                dataDict = cgi.parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                qs = self.rfile.read(length)
                dataDict = cgi.parse_qs(qs, keep_blank_values=1)
            # remove things such as boundary specfiers
            #print "dataDict -> ", dataDict
            data = dataDict['data'][0]
            #print "data: ", data
            msgs = json.loads(data)
            #print "msgs:", msgs
            for msg in msgs:
                #print "msg: ", msg
                self.server.hub.handleMessage(self, msg, None, None)
	    self.wfile.write("numMessages:\n%s\n" % len(msgs))
            self.wfile.write("\n")
	    return
        print "Unknown POST url path:", path
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
	self.wfile.write("Unknown POST path: " + path)

    def do_GET(self):
        #print "*** do GET ***"
	path = self.path
	qstr = ""
	dict = {}
	try:
	    idx = string.index(path, "?")
	    qstr = path[idx+1:]
	    path = path[:idx]
	    #print "path:", path
	    #print "qstr:", qstr
	    try:
                um = URLMarshaller()
                dict = um.unmarshal(qstr)
            except:
		print "Bad Query String:", qstr
	    #print "dict:", dict
	except ValueError:
	    pass
        if path == "/serverControl":
            # This is only for the purpose of controlling whether
            # hostnames get lookedup for the server log.  Sometimes
            # that can take a long time.
            self.setupReply("text/plain")
	    if dict.has_key('lookupHostnames'):
                val = dict['lookupHostnames']
	        if val == '0' or val.lower() == 'false':
	            print "Turning off hostname lookup"
	            self.server.lookupHostnames = 0
	        else:
	            print "Turning on hostname lookup"
	            self.server.lookupHostnames = 1
	    self.wfile.write("ok")
	    return
        if path == "/postMessage" or path == "/sendMessage":
            self.setupReply("text/plain")
            try:
                msg = dict
                try:
                    if self.server.hub:
                        ms = Marshaller()
                        msgbuf = ms.marshal(msg)
                        self.server.hub.handleMessage(self, msg, msgbuf, ms.type)
                except:
	            traceback.print_exc(file=sys.stderr)
                self.wfile.write("Successful\n%s\n" % `msg`)
            except:
	        traceback.print_exc(file=sys.stderr)
	        errMsg = "error: MessageHandler Failed\n"
	        errMsg = errMsg + ("URL PATH: %s" % self.path)
	        self.wfile.write(errMsg)
	        return	    
	    return
        if BANNER_PAGE != None and (path == "" or path == "/"):
            self.path = BANNER_PAGE
	    SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)
            return
	if path == "/status" or \
               (PARANOID == 0 and (path == "" or path == "/")):
            self.setupReply("text/plain")
	    sos = StringIO.StringIO()
#	    self.server.hub.genReport(sos)
	    gen = ReportGen.ReportGenerator(self.server.hub)
	    try:
	        gen.genReport(sos)
	    except:
                traceback.print_exc(file=sys.stderr)
	        print "Error while generating report"
	    sos.seek(0)
	    str = sos.read()
	    self.wfile.write(str)
	    return
        if path == "/getServerInfo":
            self.setupReply("text/plain")
            str = "Info Not Available"
	    try:
                str = getServerInfo(self.server)
	    except:
                traceback.print_exc(file=sys.stderr)
	        print "Error while generating report"
	    self.wfile.write(str)
	    return
        if path == "/getLatestMessages":
            self.setupReply("text/plain")
            str = "Info Not Available"
	    try:
                str = getLatestMessages(self.server, dict)
	    except:
                traceback.print_exc(file=sys.stderr)
	        print "Error while generating report"
	    self.wfile.write(str)
	    return
	if path == "/fetchMessages":
            self.setupReply("text/plain")
            try:
                print dict
	        subscriptionId = dict['subscriptionId']
            except:
                traceback.print_exc(file=sys.stderr)
                errStr = "Error: BadQueryString %s\n" % `qstr`
                print errStr
	        self.wfile.write(errStr)
	        return
	    #print "fetch", subscriptionId
	    try:
	        subscriptionHandler = self.server.hub.peerHandlerDict[subscriptionId]
		msgs = subscriptionHandler.retrieveStoredMessages()
	        self.wfile.write("# Returning messages for %s\n" % subscriptionId)
	    	self.wfile.write("# NumStored: %d\n" % len(msgs))
		marshaller = Marshaller()
	        for msg in msgs:
	            str = marshaller.marshal(msg)
	            print "Sending:", str
	            self.wfile.write("%s\n" % str)
	    except KeyError:
	        print "************************************"
                errStr = "Error: NoSuchSubscription %s\n" % subscriptionId
	        print "Failed fetch... ", errStr
	    	self.wfile.write(errStr)
	    self.wfile.flush()
	    return
	if path == "/jsonFetchMessages":
            self.setupReply("text/plain")
            try:
	        subscriptionId = dict['subscriptionId']
            except:
                traceback.print_exc(file=sys.stderr)
	        self.wfile.write("Bad Query String: '%s'\n" % `qstr`)
	        return
	    # print "fetch", subscriptionId
	    try:
	        subscriptionHandler = self.server.hub.peerHandlerDict[subscriptionId]
		msgs = subscriptionHandler.retrieveStoredMessages()
		marshaller = JSONMarshaller()
                buf = marshaller.marshalMessages(msgs)
                #print "sending: "+buf
                self.wfile.write("%s\n" % buf)
	    except KeyError:
                errStr = "Error: NoSuchSubscription %s\n" % subscriptionId
                errMsg = {'msgType': 'system.error',
                          'subscriptionId': subscriptionId,
                          'error': 'NoSubscription'}
                msgs = [errMsg]
		marshaller = JSONMarshaller()
                buf = marshaller.marshalMessages(msgs)
                #print "sending: "+buf
	        print "*** Failed fetch... ", errStr
                print "sending:", buf
                self.wfile.write("%s\n" % buf)
	    self.wfile.flush()
	    return
	if path == "/jsFetchMessages":
            self.setupReply("text/plain")
            try:
	        subscriptionId = dict['subscriptionId']
            except:
                traceback.print_exc(file=sys.stderr)
	        self.wfile.write("Bad Query String: '%s'\n" % `qstr`)
	        return
	    # print "fetch", subscriptionId
	    self.wfile.write("<html>\n")
	    self.wfile.write("<head>\n")
	    numMessages = 0
	    try:
	        subscriptionHandler = self.server.hub.peerHandlerDict[subscriptionId]
		msgs = subscriptionHandler.retrieveStoredMessages()
	    	self.wfile.write("//Num Stored: %d\n" % len(msgs))
		marshaller = JavaScriptMarshaller()
	        numMessages = len(msgs)
	        for msg in msgs:
	            str = marshaller.marshal(msg)
	            print "Sending:", str
	            self.wfile.write("%s\n" % str)
	    except KeyError:
	        print "************************************"
                errStr = "Error: NoSuchSubscription %s\n" % subscriptionId
	        print "Failed fetch... ", errStr
	    	self.wfile.write(errStr)
	    self.wfile.write("</head>\n")
	    self.wfile.write("<body>\n")
	    self.wfile.write('<script language="JavaScript">\n')
	    self.wfile.write('top.mb_status = "completed";\n')
	    self.wfile.write('</script>\n')
	    self.wfile.write("%d messages\n" % numMessages)
	    self.wfile.write("</body>\n")
	    self.wfile.write("</html>\n")
	    self.wfile.flush()
	    return
	if path == "/xmlFetchMessages":
            self.setupReply("text/xml")
            try:
	        subscriptionId = dict['subscriptionId']
            except:
                traceback.print_exc(file=sys.stderr)
	        self.wfile.write("Bad Query String: '%s'\n" % `qstr`)
	        return
	    print "fetch", subscriptionId
	    self.wfile.write('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
	    self.wfile.write('<messages>\n')
	    numMessages = 0
	    try:
	        subscriptionHandler = self.server.hub.peerHandlerDict[subscriptionId]
		msgs = subscriptionHandler.retrieveStoredMessages()
	    	#self.wfile.write("<-- Num Stored: %d -->\n" % len(msgs))
		marshaller = XMLMarshaller()
	        numMessages = len(msgs)
	        for msg in msgs:
	            str = marshaller.marshal(msg)
	            print "Sending:", str
	            self.wfile.write("%s\n" % str)
	    except KeyError:
	        print "************************************"
                errStr = "<error>NoSuchSubscription %s</error>\n" % subscriptionId
	        print "Failed fetch... ", errStr
	    	self.wfile.write(errStr)
	    self.wfile.write('</messages>\n')
	    self.wfile.flush()
	    return
	if path == "/watchMessages":
            self.setupReply("text/plain")
	    patternMsg = dict
	    self.server.hub.registerPeerHandler(self, patternMsg)
	    self.wfile.write("#Pattern: %s\n" % `patternMsg`)
	    self.wfile.write("#Watching:\n")
	    self.wfile.flush()
	    self.running = 1
	    # Now this thread can't do anthing more, and must
            # let other threads do the work of sending messages.
	    while self.running:
		time.sleep(2)
	    return
	if path == "/jsWatchMessages":
            self.setupReply("text/html")
	    patternMsg = dict
	    self.server.hub.registerPeerHandler(self, patternMsg)
	    self.wfile.write("<html>\n")
	    self.wfile.write("<head>\n")
	    self.wfile.write("</head>\n")
	    self.wfile.write("<body>\n")
	    self.wfile.write("<h3>Pattern: %s</h3>\n" % `patternMsg`)
	    self.wfile.flush()
	    self.marshaller = JavaScriptMarshaller()
	    self.running = 1
	    # Now this thread can't do anthing more, and must
            # let other threads do the work of sending messages.
	    while self.running:
		time.sleep(2)
	    return
	if path == "/xmlWatchMessages":
            self.setupReply("text/xml")
	    patternMsg = dict
	    self.server.hub.registerPeerHandler(self, patternMsg)
	    self.wfile.write('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
	    self.wfile.write("<messages>\n")
	    self.wfile.flush()
	    self.marshaller = XMLMarshaller()
	    self.running = 1
	    # Now this thread can't do anthing more, and must
            # let other threads do the work of sending messages.
	    while self.running:
		time.sleep(2)
	    return
	if path == "/help":
	    self.setupReply("text/html")
	    self.wfile.write(helpHtmlStr)
	    return
	if PARANOID:
	    self.do_sendClientInfo()
	    return
	if qstr != "" and not ALLOW_QSTR_ON_SIMPLE_REQUESTS:
  	    self.wfile.write(errorHtmlStr % self.path)
	    return
	else:
            #print "**************************************"
            #print "path:", path
            self.path = path
	    SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)

    def do_sendClientInfo(self):
	self.setupReply("text/plain")
        self.wfile.write("HTTP Server not operating\n")
  	self.wfile.write("Request: %s %s\n" % (self.path, self.clientAddressStr))

    def setupReply(self, mimeType):
        self.send_response(200)
        self.send_header("Content-type", mimeType)
        self.end_headers()

    def sendMessage(self, msg, msgbuf, marshallType):
	print "httphandler.sendMessage..."
	if msgbuf == None or marshallType != self.marshaller.type:
	    msgbuf = self.marshaller.marshal(msg)
	self.wfile.write(msgbuf+"\n")
	self.wfile.flush()
	self.numSent += 1
	self.lastSent = msg


class ThreadedHTTPServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer, Gateway):
    pass

def runHTTPServer_(server):
    sa = server.socket.getsockname()
    print "Running HTTP   gateway on port", sa[1]
    sys.stdout.flush()
    server.serve_forever()

def runHTTPServer(server=None, useThread=0, messageHandlerFactory=SimpleMessageHandler, hub=None, port=-1):
    http_port = MessageBoard.MESSAGE_BOARD_HTTP_PORT
    if port > 0:
	http_port = port

    if server == None:
        handlerClass = HANDLER_CLASS
        if handlerClass == None:
            handlerClass = HTTPMessageRequestHandler
        server_address = ('', http_port)
        server = ThreadedHTTPServer(server_address, handlerClass)
	server.lookupHostnames = 1
        server.hub = hub
    if useThread:
        thread = threading.Thread(target=runHTTPServer_, args=(server,))
        thread.setDaemon(1)
        thread.start()
        return thread
    else:
        runHTTPServer_(server)


