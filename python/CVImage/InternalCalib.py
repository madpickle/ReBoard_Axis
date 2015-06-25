# -*- coding: utf-8 -*-

import os, sys
import cv2
import numpy as np
import json

class InternalCalib:
    #paramFilePath: file path of parameter file
    #imageSize: [width, height] of image
    def __init__(self, paramFilePath, imageSize=None):
        self.calibParam = {'imageSize': [400, 300],\
                      'principalPoint': [200., 150.],\
                      'focalLength': [100., 100.],\
                      'distortion': [0., 0., 0., 0.]}
        self.imageSize = [400, 300]

        self.cameraMatrix = np.array([[200., 0., 100.],\
                                     [0., 150., 100.],\
                                     [0., 0., 1.]])
        self.distCoeffs = np.array([0., 0., 0., 0.])

        self.loadCalibParam(paramFilePath)
        self.setImageSize(imageSize)

    def loadCalibParam(self, filePath):
        f = open(filePath)
        self.calibParam = json.load(f)
        f.close()

        self.setImageSize()

    def setImageSize(self, imageSize=None):
        wScale = 1.0
        hScale = 1.0

        if imageSize != None:
            wScale = float(imageSize[0])/float(self.calibParam['imageSize'][0])
            hScale = float(imageSize[1])/float(self.calibParam['imageSize'][1])

        if wScale != hScale:
            print "image aspect ratio error"
            return

        s = wScale

        self.imageSize = imageSize

        self.cameraMatrix = [[self.calibParam['focalLength'][0] * s, 0., self.calibParam['principalPoint'][0] * s],\
                             [0., self.calibParam['focalLength'][1] * s, self.calibParam['principalPoint'][1] * s],\
                             [0., 0., 1.]]
        self.cameraMatrix = np.array(self.cameraMatrix)

        self.distCoeffs = self.calibParam['distortion']
        self.distCoeffs = np.array(self.distCoeffs)

    def undistort(self, srcImg):
        dstImg = cv2.undistort(srcImg, self.cameraMatrix, self.distCoeffs)
        return dstImg


