/*

JavaScript MessageBoard package.

*/

var mb_debugWin = null;
var mb_debug = 0;
var mb_serverHost = "mbserver:8010";
var mb_resultsWin = "control";
//var mb_pushResultsWin = "pushResults";
//var mb_pushResultsWin = "control";
var mb_pushResultsWin = "results";
var mb_numTicks = 0;
var mb_date = new Date();
var mb_subId = "client"+mb_date.getTime();
var mb_client = null;
var mb_amPolling = false;
var mb_useJS = true;
var mb_pollingInterval = 1.0;  // in seconds
/*
var mb_isIE = false;
if (document.all)
   mb_isIE = true;
*/
var mb_isIE = (navigator.appName == "Microsoft Internet Explorer");

function mb_setDebugLevel(level)
{
   mb_debug = level;
}

function mb_setPollingInterval(t)
{
    mb_pollingInterval = t;
}

function report(str)
{
   if (mb_debug == 0)
      return;
   if (mb_debugWin == null) {
      mb_debugWin = open("", "debug");
      mb_debugWin.document.open("text/plain");
   }
   if (mb_debugWin != null) {
      for (var i=0; i<5; i++) {
          try {
              mb_debugWin.document.writeln(str);
	      if (!mb_isIE)
                 mb_debugWin.document.writeln("<br>");
              break;
          }
          catch (e) {
              mb_debugWin = open("", "debug");
              mb_debugWin.document.open("text/plain");
          }
      }
   }
}

function reportError(str)
{
    report(str);
}

function mb_fetchUrlToWindow(url, winName) {
    if (mb_debug > 1)
        report("URL = "+url+"\n");
    open(url, winName);
}

function mb_fetchUrl(url) {
    if (mb_debug > 1)
        report("URL = "+url+"\n");
    try{
       if (mb_isIE)
           mb_loadDoc(url);
       else {
          //mb_fetchUrlToWindow(url, "dummy");
          try {
              netscape.security.PrivilegeManager.enablePrivilege("UniversalBrowserRead");
          }
          catch (err) {
              report("Cannot get UniversalBrowserRead prvilege");
              report(""+err);
          }
          mb_loadDoc(url);
       }
    }
    catch (err) {
       report("mb_fetchUrl:error: "+err);
    }
}


/*
  This function takes two forms:

     mb_sendMessage(message);
     mb_sendMessage(name1, val1, name2, val2, ...)

*/
function mb_sendMessage() {
    var key, val, i;
    var nargs = arguments.length;
    var url = "http://"+mb_serverHost+"/sendMessage?";
    if (nargs == 1) {
        var msg = arguments[0];
        var numFields = 0;
        for (var key in msg)
           numFields++;
        i = 0;
        for (var key in msg) {
            val = escape(msg[key]);
            key = escape(key);
            url += key + "=" + val;
            if (i < numFields - 1)
                url += "&";
            i++;
        }
        var gen = mb_genUniqueId();
        url += "&system.gen="+gen;
        mb_fetchUrl(url);
	return;
    }
    if (nargs % 2 == 1 || nargs == 0) {
        reportError("sendMessage needs even number of arguments > 0");
        //report("nargs: "+nargs);
        //report("args: "+arguments);
        return;
    }
    for (i=0; i<nargs; i += 2) {
        key = escape(arguments[i]);
        val = escape(arguments[i+1]);
	url += key + "=" + val;
        if (i < nargs - 2)
           url += "&";
    }
    var gen = mb_genUniqueId();
    url += "&system.gen="+gen;
    mb_fetchUrl(url);
}

function mb_genUniqueId() {
    var date = new Date();
    return date.getTime();
}

function mb_startServerPush() {
   mb_fetchUrlToWindow("http://"+mb_serverHost+"/jsWatchMessages", mb_pushResultsWin);
}

function mb_registerHandler(handler, pattern) {
    handler.pattern = pattern;
    mb_client.handlers.push(handler);
}

function mb_copy(msg) {
    var newMsg = new Object();
    for (var key in msg)
        newMsg[key] = msg[key];
    return newMsg;
}

function mb_sendPatternMessages()
{
    mb_sendMessage("system.msgType", "subscribe",
                   "system.subscriptionId", mb_subId);
    mb_sendMessage("system.msgType", "pattern.clear",
                   "system.subscriptionId", mb_subId);
    for (var i=0; i<mb_client.handlers.length; i++) {
        var msg = mb_copy(mb_client.handlers[i].pattern);
        msg["system.msgType"] = "pattern.add";
        msg["system.subscriptionId"] = mb_subId;
        mb_sendMessage(msg);
    }
    mb_client.subscribed = true;
}

function mb_startPolling() {
    mb_sendPatternMessages();
    mb_amPolling = true;
    setTimeout('mb_handleTimeout();', 2000);
}

function mb_startPollingXML() {
   report("mb_startPollingXML");
   mb_useJS = false;
   mb_startPolling();
}

function mb_handleTimeout()
{
   var url;
   mb_numTicks++;
   if (!mb_amPolling) {
	report("finished polling");
	return;
   }
   if (!mb_client.subscribed) {
      mb_sendPatternMessages();
   }
   var gen = mb_genUniqueId();
   var interval = Math.floor(1000 * mb_pollingInterval);
   setTimeout('mb_handleTimeout();', interval);
   if (mb_useJS) {
      if (top.mb_status == "started")
	  mb_client.subscribed = false;
      url = "http://"+mb_serverHost+
            "/jsFetchMessages?subscriptionId="+mb_subId+
            "&system.gen="+gen;
      top.mb_status = "started";
      mb_fetchUrlToWindow(url, mb_resultsWin);
   }
   else {
      url = "http://"+mb_serverHost+
            "/xmlFetchMessages?subscriptionId="+mb_subId+
            "&system.gen="+gen;
      mb_loadXML(url);
   }
}

/*
   Return true iff str == pstr or pstr ends with *
   and str starts the part of pstr before the *
*/
function mb_stringMatches(pstr, str)
{
    if (pstr == str)
        return true;
    var plen = pstr.length;
    if (plen == 0 || pstr.charAt(plen-1) != "*")
        return false;
    if (str.length < plen-1)
        return false;
    return str.substring(0, plen-1) == pstr.substring(0, plen-1);
}

/*
   Return true if ever key of pattern is found in msg
   and with a matching value.
*/
function mb_matches(pattern, msg)
{
    for (var key in pattern) {
        if (msg[key] == "undefined")
	    return false;
	if (!mb_stringMatches(pattern[key], msg[key]))
            return false;
    }
    return true;
}

/*
  These are just for debugging.
*/
function mb_testStringMatches(pstr, str)
{
    report("matches '"+pstr+"', '"+str+"'  --> " + mb_stringMatches(pstr, str));
}

function mb_testMatches(pattern, msg)
{
    report("Matching\nPattern:")
    mb_dumpMessage(pattern);
    report("Msg:")
    mb_dumpMessage(msg);
    report("matches --> " + mb_matches(pattern, msg));
    report("");
}


function mb_noticeMessage(msg) {
   if (mb_debug > 1) {
      report("noticeMessage:"+msg+"  msgType:"+msg["msgType"]);
      if (mb_debug > 2) {
          mb_dumpMessage(msg);
      }
   }
   if (mb_client == null) {
      report("mb_noticeMessage:"+msg);
      mb_dumpMessage(msg);
      return;
   }
   for (var i=0; i<mb_client.handlers.length; i++) {
       var handler = mb_client.handlers[i];
       if (mb_debug > 1)
           mb_testMatches(handler.pattern, msg);
       if (mb_matches(handler.pattern, msg))
           handler(msg);
   }
}

function mb_stopClient() {
   mb_amPolling = false;
   var gen = mb_genUniqueId();
   url = "http://"+mb_serverHost+"/help?system.gen="+gen;
   mb_fetchUrlToWindow(url, mb_pushResultsWin);
}

function Message()
{
    nargs = arguments.length;
    if (nargs % 2 == 1 || nargs == 0) {
        reportError("Message needs even number of arguments");
        return;
    }
    var msg = new Object();
    for (i=0; i<nargs; i += 2) {
        var key = escape(arguments[i]);
        var val = escape(arguments[i+1]);
        msg[key] = val;
    }
    return msg;
}

Pattern = Message;

function mb_dumpMessage(msg)
{
    report("{");
    for (var key in msg) {
        report("'"+key+"': '"+msg[key]+"'");
    }
    report("}");
}

function mb_login(userName, password)
{
    mb_client.userName = userName;
    mb_client.password = password;
}

function MessageBoardClient(server)
{
    mb_serverHost = server;
    var client = new Object();
    client.sendMessage = mb_sendMessage;
    client.handlers = new Array();
    mb_client = client;
    client.subscribed = false;
    client.setDebugLevel = mb_setDebugLevel;
    client.setPollingInterval = mb_setPollingInterval;
    client.startServerPush = mb_startServerPush;
    client.startPolling = mb_startPolling;
    client.startPollingXML = mb_startPollingXML;
    client.start = mb_startPollingXML;
    client.stop = mb_stopClient;
    client.registerHandler = mb_registerHandler;
    client.dumpMessage = mb_dumpMessage;
    client.login = mb_login;
    return client;
}


function mb_XML_to_JS(req, containerTag)
{
   //report("Reply: "+req.responseText);
   var xmlDoc = req.responseXML;
   var messages = new Array();
   var errorRecords = xmlDoc.getElementsByTagName("error");
   if (errorRecords.length > 0) {
       report("Got error from server");
       return null;
   }
   if (xmlDoc.getElementsByTagName("messages").length == 0) {
       report("No messages tag...");
       return null;
   }
   var messageRecords = xmlDoc.getElementsByTagName("message");
   //report("num message records: "+messageRecords.length);
   for (var i=0; i<messageRecords.length; i++) {
      var messageRecord = messageRecords[i];
      var fields = messageRecord.getElementsByTagName("field");
      var msg = messages[messages.length] = new Object();
      for (var j=0; j<fields.length; j++) {
          var field = fields[j];
          var key = field.getElementsByTagName("name")[0].firstChild.nodeValue;
          var valueNode =  field.getElementsByTagName("value")[0].firstChild;
          var value = "";
	  if (valueNode != null)
              value = valueNode.nodeValue;
          msg[key] = value;
      }
   }
   return messages;
}

/*
function mb_loadXML(url)
{
    var xmlDoc;
    if (document.implementation && document.implementation.createDocument)
    {
	xmlDoc = document.implementation.createDocument("", "", null);
	xmlDoc.onload = function () { mb_handleCompletedLoad(xmlDoc) };
    }
    else if (window.ActiveXObject)
    {
	xmlDoc = new ActiveXObject("Microsoft.XMLDOM");
	xmlDoc.onreadystatechange = function () {
		if (xmlDoc.readyState == 4) mb_handleCompletedLoad(xmlDoc)
	};
    }
    else
    {
	alert("Your browser can't handle this script");
	return;
    }
    xmlDoc.load(url);
}
*/

var req;

function mb_loadXML(url) {
    req = false;

    if (!mb_isIE) {
       try {
          netscape.security.PrivilegeManager.enablePrivilege("UniversalBrowserRead");
       }
       catch (err) {
           report("Cannot get UniversalBrowserRead prvilege");
           report(""+err);
       }
    }

    // branch for native XMLHttpRequest object
    if(window.XMLHttpRequest) {

       if (!mb_isIE) {
          try {
             netscape.security.PrivilegeManager.enablePrivilege("UniversalBrowserRead");
          }
          catch (err) {
             report("Cannot get UniversalBrowserRead prvilege");
             report(""+err);
          }
        }

    	try {
	    req = new XMLHttpRequest();
        } catch(e) {
	    req = false;
        }
    // branch for IE/Windows ActiveX version
    } else if(window.ActiveXObject) {
       	try {
            req = new ActiveXObject("Msxml2.XMLHTTP");
      	} catch(e) {
            try {
          	req = new ActiveXObject("Microsoft.XMLHTTP");
            } catch(e) {
          	req = false;
            }
	}
    }
    if(req) {
	//req.onreadystatechange = processReqChange;
	req.onreadystatechange = function () {
	    if (req.readyState == 4)
	        mb_handleCompletedLoad(req)
	};
	req.open("GET", url, true);
        req.send(null);
    }
}

//
// Calling this won't work.... because permissions are cleared after
// return.  Instead, it is necessay to use this code before each place
// that will need the permissions.
//
/*
function mb_preparePermissions()
{
    if (!mb_isIE) {
       try {
          netscape.security.PrivilegeManager.enablePrivilege("UniversalBrowserRead");
       }
       catch (err) {
           report("Cannot get UniversalBrowserRead prvilege: " + err);
       }
   }
}
*/

function mb_handleCompletedLoad(req)
{
    if (!mb_isIE) {
       try {
          netscape.security.PrivilegeManager.enablePrivilege("UniversalBrowserRead");
       }
       catch (err) {
           report("Cannot get UniversalBrowserRead prvilege");
           report(""+err);
       }
    }

    var data = mb_XML_to_JS(req, "messageList");
    if (data == null) {
	mb_client.subscribed = false;
        return;
    }
    for (var i in data) {
        var msg = data[i];
        mb_noticeMessage(msg);
    }
}

var req2 = null;

function mb_loadDoc(url) {
    req2 = false;
    // branch for native XMLHttpRequest object
    if(window.XMLHttpRequest) {
    	try {
	    req2 = new XMLHttpRequest();
        } catch(e) {
	    req2 = false;
        }
    // branch for IE/Windows ActiveX version
    } else if(window.ActiveXObject) {
       	try {
            req2 = new ActiveXObject("Msxml2.XMLHTTP");
      	} catch(e) {
            try {
          	req2 = new ActiveXObject("Microsoft.XMLHTTP");
            } catch(e) {
          	req2 = false;
            }
	}
    }
    if(req2) {
	//req2.onreadystatechange = processReqChange;
	req2.onreadystatechange = function () {
	    if (req2.readyState == 4)
	        mb_dummyCompletion(req2)
	};
	req2.open("GET", url, true);
        req2.send(null);
    }
}


function mb_dummyCompletion(req)
{
//    report("completed");
}

top.mb_noticeMessage = mb_noticeMessage;
top.mb_status = "initial";


