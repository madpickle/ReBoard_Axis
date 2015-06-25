
import ObjectShare
ObjectShare.DEFAULT_MESSAGE_BOARD_HOST
ObjectShare.DEFAULT_MESSAGE_BOARD_HOST = "mbserver"
oc = ObjectShare.ObjectShareClient()
print "Got Object Share Client", oc

box=oc.getObject("box")
#box=oc.getObject("object-box1")
print "got box:", box
print "Color of box was:", box['color']
box['color'] = 'blue'
print "Color of box is now:", box['color']

