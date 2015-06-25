# -*- coding: utf-8 -*-

# This is a sample to get cropped white board image


import os, sys
import cv2
import numpy as np
import time

sys.path.append("../../../")

from RoomCapture import WhiteBoardClient

paramFile = "OpenLab_WhiteBoard.json"


###################

whiteBoardClient = WhiteBoardClient.WhiteBoardClient(paramFile)

whiteBoardClient.startMovementCheckThread()
time.sleep(3)

whiteBoardClient.diffCheckProcess()


