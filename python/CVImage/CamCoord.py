# -*- coding: utf-8 -*-

# カメラの座標関連

import os,sys

import os,sys
import json
import math
import numpy as np

sys.path.append('../')
from CVImage import CoordinateTransform3D


class CamCoord:
    def __init__(self):

        #レンズ中心
        self.imageCenter = np.array([0.5, 0.5])

        #焦点距離
        self.foculDistance = np.array([1.0, 1.0])

        #カメラ位置
        self.coordinateTransform = CoordinateTransform3D.CoordinateTransform3D()

    # レンズ中心の設定 imageCenter=[0.5, 0.5]
    def setImageCenter(self, imageCenter):
        self.imageCenter = np.array(imageCenter)

    def setFoculdistance(self, foculDistance):
        self.foculDistance = np.array(foculDistance)

    def setFieldOfView(self, fov):
        tanFov = np.array([math.tan(math.radians(fov[0]*0.5)), math.tan(math.radians(fov[1]*0.5))])
        self.foculDistance = 0.5 / tanFov

    def setCameraPose(self, T, pan, tilt, roll):
        self.coordinateTransform.setT(T)
        self.coordinateTransform.setPanTiltRoll(pan, tilt, roll)

    def getCameraPos(self):
        return self.coordinateTransform.getT()

    #convert image pos [x, y] to image pos on camera
    def iPos2calibImagePos(self, iPos):
        iPos = np.array(iPos)

        calibImagePos = (iPos - self.imageCenter)

        return calibImagePos

    #convert image pos on camera [x,y] to image pos
    def calibImagePos2iPos(self, calibImagePos):
        calibImagePos = np.array(calibImagePos)

        iPos =  (calibImagePos + self.imageCenter)

        return iPos


    #convert image pos [x, y] to camera coordinate direction [x, y, 1]
    def iPos2cPos(self, iPos, z=1.0):
        calibImagePos = self.iPos2calibImagePos(iPos)
        cPos = calibImagePos/self.foculDistance

        return cPos

    #convert camera coordinate direction [x, y, 1] to image pos [x, y]
    def cPos2iPos(self, cPos):
        cPos = cPos / cPos[2] #normalize by z values
        calibImagePos = cPos[:2]
        calibImagePos = calibImagePos * self.foculDistance

        return self.calibImagePos2iPos(calibImagePos)

    def iPos2wPos(self, iPos, z=1000.0):
        cPos = self.iPos2cPos(iPos, z)

        wPos = self.coordinateTransform.transform(cPos)
        return wPos

    def wPos2iPos(self, wPos):
        invTransform = self.coordinateTransform.inverse()
        cPos = invTransform.transform(wPos)

        return self.cPos2iPos(cPos)

    def iPos2iPosPixel(self, iPos, img):
        height, width = img.shape[:2]
        return self.iPos2iPosPixel_shape(iPos, width, height)

    def iPos2iPosPixel_shape(self, iPos, width, height):
        imSize = np.array([width, height])
        iPosPixel = imSize * iPos
        return iPosPixel.astype(np.int)

    #オブジェクトに対応する画像座標(4 corners)を計算する
    # wpt: objectの位置[x,y,z]
    # wSize: objectの大きさ width (mm)
    # hSize: objectの大きさ height (mm)
    # zTopMargin: objectの一番上と画像の一番上との隙間 (mm)
    # angleFixLevel: 1:通常、2: Pan/Tiltのみカメラと同じ、3: Panだけカメラと同じ
    def calcCropImageCoords(self, wpt, wSize, hSize, zTopMargin = 0.0, angleFixLevel = 1):
        """
        rect = [[-0.5 * wSize,  -0.5 * hSize, 0.5 * wSize],\
                [-0.5 * wSize,   0.5 * hSize, 0.5 * wSize],\
                [ 0.5 * wSize,   0.5 * hSize, 0.5 * wSize],\
                [ 0.5 * wSize,  -0.5 * hSize, 0.5 * wSize]]
                """
        rect = [[-0.5 * wSize,  -0.5 * hSize, 0.],\
                [-0.5 * wSize,   0.5 * hSize, 0.],\
                [ 0.5 * wSize,   0.5 * hSize, 0.],\
                [ 0.5 * wSize,  -0.5 * hSize, 0.]]
        rect = np.array(rect)


        wpt[2] = wpt[2] - hSize*0.5 + zTopMargin

        pan, tilt, roll = self.coordinateTransform.getPanTiltRoll()

        obTransform = CoordinateTransform3D.CoordinateTransform3D()
        obTransform.setT(wpt)
        if angleFixLevel == 2:
            obTransform.setPanTiltRoll(pan, tilt, 0.0)
        elif angleFixLevel == 3:
            obTransform.setPanTiltRoll(pan, 0.0, 0.0)
        else:
            obTransform.setPanTiltRoll(pan, tilt, roll)

        iPoints = []
        for i in xrange(4):
            obRect = obTransform.transform(rect[i])
            iPoint = self.wPos2iPos(obRect)
            iPoints.append(iPoint)

        return iPoints



