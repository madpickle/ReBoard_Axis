# -*- coding: utf-8 -*-

# This is a sample to get cropped white board image


import os, sys
import cv2
import numpy as np

sys.path.append("../../../")

from RoomCapture import WhiteBoardClient

paramFile = "OpenLab_WhiteBoard.json"

###################

whiteBoardClient = WhiteBoardClient.WhiteBoardClient(paramFile)

# get HD cropped image
img = whiteBoardClient.getImg()
cv2.imwrite("img.jpg", img)

# get smaller cropped image for checking movements
movementCheckImg = whiteBoardClient.getMovementCheckImg()
cv2.imwrite("movementCheckImg.jpg", movementCheckImg)
