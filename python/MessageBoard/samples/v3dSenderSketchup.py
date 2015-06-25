from time import *
import MessageBoard
portal = MessageBoard.MessageClient("localhost")

sleep_times = 2

#### line1

msg = {'msgType': 'v3d.create',
       'className': 'LineSet', 
       'name': 'line1',
       'linePoints': ((0,0,0),(10,0,0),(10,10,0),(0,10,10))}
portal.sendMessage(msg)

sleep(sleep_times)

msg = {'msgType': 'v3d.setProps', 
       'name': 'line1',
       'linePoints': ((10,0,10),(0,10,10),(10,0,0),(0,0,10))}
portal.sendMessage(msg)

sleep(sleep_times)

msg = {'msgType': 'v3d.setProps', 
       'name': 'line1',
       'translation': (10,10,10),
       'orientation': (1, 0, 0, 1.57)}
portal.sendMessage(msg)

sleep(sleep_times)

#### face1

msg = {'msgType': 'v3d.create',
       'className': 'FaceSet', 
       'name': 'face1',
       'facePoints': ((0,0,0),(0,10,0),(0,10,10),(0,0,10)),
       'color': (255,100,43)}
portal.sendMessage(msg)

sleep(sleep_times)

msg = {'msgType': 'v3d.setProps', 
       'name': 'face1',
       'facePoints': ((0,-10,-10),(0,-10,10),(0,10,10),(0,10,-10)),
       'color': (5,250,123),
       'transparency': 0.7}
portal.sendMessage(msg)

sleep(sleep_times)

msg = {'msgType': 'v3d.setProps', 
       'name': 'face1',
       'translation': (-10,-10,-10),
       'orientation': (0, 1, 0, -0.8)}
portal.sendMessage(msg)

sleep(sleep_times)

#### marker1

msg = {'msgType': 'v3d.create',
       'className': 'Image', 
       'name': 'marker1',
       'filePath': 'D:/pantheia/src/ARToolKitPlus/ARToolKitPlus_AllMarkers/marker_001_x10.png',
       'imageWidth': 10, 'imageHeight': 10}
portal.sendMessage(msg)

sleep(sleep_times)

msg = {'msgType': 'v3d.setProps', 
       'name': 'marker1',
       'translation': (0,0,30),
       'orientation': (1, 0, 0, 0.3),
       'transparency': 0.7}
portal.sendMessage(msg)

sleep(sleep_times)

#### marker2

msg = {'msgType': 'v3d.create',
       'className': 'Image', 
       'name': 'marker2',
       'filePath': 'D:/pantheia/src/ARToolKitPlus/ARToolKitPlus_AllMarkers/marker_002_x10.png',
       'imageWidth': 10, 'imageHeight': 10,
       'translation': (30,0,0),
       'orientation': (1, 0, 0, -1.57),}
portal.sendMessage(msg)

sleep(sleep_times)

msg = {'msgType': 'v3d.enableLayer',
       'name': 'marker2',
       'enabled': False}
portal.sendMessage(msg)

sleep(sleep_times)

msg = {'msgType': 'v3d.enableLayer',
       'name': 'marker2',
       'enabled': True}
portal.sendMessage(msg)

sleep(sleep_times)

#### marker3

msg = {'msgType': 'v3d.create',
       'className': 'Image', 
       'name': 'marker3',
       'filePath': 'D:/pantheia/src/ARToolKitPlus/ARToolKitPlus_AllMarkers/marker_003_x10.png',
       'imageWidth': 20, 'imageHeight': 20}
portal.sendMessage(msg)

sleep(sleep_times)

#### camera view

msg = {'msgType': 'v3d.setView',
       'position': (0,0,100),
       'orientation': (0,0,0,0)}
portal.sendMessage(msg)

sleep(sleep_times)

msg = {'msgType': 'v3d.setView',
       'position': (0,0,0),
       'orientation': (0,0,0,0),
       'animationTime': sleep_times}
portal.sendMessage(msg)

sleep(sleep_times)

msg = {'msgType': 'v3d.setView',
       'position': (0,-100,100),
       'orientation': (1,0,0,0.4),
       'animationTime': sleep_times}
portal.sendMessage(msg)

sleep(sleep_times)

msg = {'msgType': 'v3d.setView',
       'vfov': 56.78}
portal.sendMessage(msg)

sleep(sleep_times)

msg = {'msgType': 'v3d.setView',
       'position': (0,0,100),
       'orientation': (0,0,0,0),
       'animationTime': sleep_times}
portal.sendMessage(msg)

sleep(sleep_times)
