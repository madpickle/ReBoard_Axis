# -*- coding: utf-8 -*-

# This is a sample to get an image from AXIS camera and undistort it


import os, sys
import cv2
import numpy as np

sys.path.append("../../../")

from CVImage import InternalCalib
from CVImage import HttpGetImage

#AXIS URL
url = "http://192.168.104.208/axis-cgi/jpg/image.cgi?resolution=2048x1536&compression=10"
#url = "http://192.168.104.208/axis-cgi/jpg/image.cgi?resolution=1024x768&compression=10"

#Camera Internal parameter file for AXIS P1346
internalParamFile = "AXIS_P1346_internalParam.json"

#size of the camera image
imageSize = [2048, 1536]
#imageSize = [1024, 768]


###################

#Get an image
httpImageClient = HttpGetImage.HttpGetImage(url)
cameraImg = httpImageClient.getImage()

#undistort the image
internalCalib = InternalCalib.InternalCalib(internalParamFile, imageSize)
undistCameraImg = internalCalib.undistort(cameraImg)

#save those images
cv2.imwrite("cameraImage.jpg", cameraImg)
cv2.imwrite("undistortCameraImage.jpg", undistCameraImg)
