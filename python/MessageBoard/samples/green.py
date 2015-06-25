
import ObjectShare
oc = ObjectShare.ObjectShareClient()

box=oc.getObject("box")
box['color'] = 'green'

