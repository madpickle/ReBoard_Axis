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

whiteBoardClient.movementCheckProcess()

