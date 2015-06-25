
import xmlrpclib
s = xmlrpclib.Server("http://localhost:9500")
dict = s.postMessage({'msgType':'test.text', 'text':'Hello World', 'a':20, 'b':3})




