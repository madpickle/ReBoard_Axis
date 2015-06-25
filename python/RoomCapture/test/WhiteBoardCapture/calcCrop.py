# -*- coding: utf-8 -*-

# This is a sample to get an image from AXIS camera and undistort it


import os, sys
import cv2
import numpy as np

imageSize = [1024, 768]
crop = [[71,19], \
        [195, 523], \
        [823, 594], \
        [889, 0]]

for r in crop:
    r[0] = float(r[0])/float(imageSize[0])
    r[1] = float(r[1])/float(imageSize[1])

print crop
