
import ObjectShare

oc = ObjectShare.ObjectShareClient()

yodel = oc.getObject('yodel')
box = oc.getObject('box')

if __name__ == '__main__':
    print "yodel:", yodel
    print "box:", box
    box['color'] = 'red'
    print box
