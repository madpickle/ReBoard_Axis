# -*- coding: utf-8 -*-

import os, sys
import cv2
import numpy as np
import math
import json
import threading
import time

sys.path.append('../')

from CVImage import HttpGetImage
from CVImage import FXImageUtil
from CVImage import PointCloud3D
from CVImage import CoordinateTransform3D
from CVImage import CamCoord
from Util import FXTimeUtil
from MessageBoard import MessageBoard
from CVImage import KinectAudio
from CVImage import D3DFloorMap

class KinectClient():
    def __init__(self, kinectInfoJsonPath="KinectInfo_default.json",\
                 mbHost=MessageBoard.DEFAULT_MESSAGE_BOARD_HOST, mbPort=MessageBoard.MESSAGE_BOARD_PORT):

        self.kinectInfoVec = []
        self.kinectRGBImageClientVec = []
        self.kinectDepthImageClientVec = []
        self.kinectPointCloud3DVec = []
        self.kinectCoordinateTransformVec = []
        self.kinectRGBCamCoordVec = []

        self.kinectAudioClient = None

        self.loadKinectInfo(kinectInfoJsonPath)

        self.mbHost = mbHost
        self.mbPort = mbPort

        self.kinectNum = len(self.kinectInfoVec)

        self.initImageClient()
        self.initPointCloud3D()
        self.initCoordinateTransform3D()
        self.initKinectAudioClient()
        self.initCamCoord()

    def loadKinectInfo(self, kinectInfoJsonPath):
        f = open(kinectInfoJsonPath, 'r')
        self.kinectInfoVec = json.load(f)
        f.close()

    def initImageClient(self):
        self.kinectDepthImageClientVec = []
        self.kinectRGBImageClientVec = []

        for k in self.kinectInfoVec:
            depthUrl = k['depth']['url']
            depthFps = k['depth']['fps']
            depthHttpClient = HttpGetImage.HttpGetImage(depthUrl, flags=cv2.IMREAD_ANYDEPTH)
            depthHttpClient.startThread(depthFps)

            self.kinectDepthImageClientVec.append(depthHttpClient)

            rgbUrl = k['rgb']['url']
            rgbFps = k['rgb']['fps']
            rgbHttpClient = HttpGetImage.HttpGetImage(rgbUrl)
            rgbHttpClient.startThread(rgbFps)

            self.kinectRGBImageClientVec.append(rgbHttpClient)


    def initPointCloud3D(self):
        self.kinectPointCloud3DVec = []

        for k in self.kinectInfoVec:
            pCloud3D = PointCloud3D.PointCloud3D()
            pCloud3D.setupKinectParams(version=k['version'])
            self.kinectPointCloud3DVec.append(pCloud3D)

    def initCoordinateTransform3D(self):
        self.kinectCoordinateTransformVec = []

        for k in self.kinectInfoVec:
            cTransform = CoordinateTransform3D.CoordinateTransform3D()
            pose = k['pose']
            cTransform.setT(pose['T'])
            cTransform.setPanTiltRoll(pose['pan'], pose['tilt'], pose['roll'])
            self.kinectCoordinateTransformVec.append(cTransform)

    def initCamCoord(self):
        self.kinectRGBCamCoordVec = []

        for k in self.kinectInfoVec:
            camCoord = CamCoord.CamCoord()

            camCoord.setImageCenter([0.5, 0.5])
            kinectVersion = k['version']
            if kinectVersion==1:
                camCoord.setFieldOfView([62.0,  48.6])
            elif kinectVersion==2:
                camCoord.setFieldOfView([84.1 , 53.8])

            pose = k['pose']
            T = pose['T']
            pan = pose['pan']
            tilt = pose['tilt']
            roll = pose['roll']
            camCoord.setCameraPose(T, pan, tilt, roll)

            self.kinectRGBCamCoordVec.append(camCoord)

    def initKinectAudioClient(self):
        self.kinectAudioClient = None

        if self.mbHost == None:
            return

        msgPatternVec = []
        for k in self.kinectInfoVec:
            msgPattern = None
            if k.has_key('audioMsgPattern'):
                msgPattern = k['audioMsgPattern']
            msgPatternVec.append(msgPattern)

        self.kinectAudioClient = KinectAudio.KinectAudioClient(msgPatternVec, self.mbHost, self.mbPort)

    def getKinectNum(self):
        return self.kinectNum

    def checkIdx(self, idx):
        if idx<0 or idx>=self.kinectNum:
            return False
        return True

    def getDepthImg(self, idx):
        if self.checkIdx(idx) == False:
            return None

        depthImg = self.kinectDepthImageClientVec[idx].getCurrentImage()
        return depthImg

    def getPointCloud(self, idx):
        depthImg = self.getDepthImg(idx)
        if depthImg == None:
            return []

        points = self.kinectPointCloud3DVec[idx].loadKinectImage(depthImg)

        T = self.kinectCoordinateTransformVec[idx].T
        R = self.kinectCoordinateTransformVec[idx].R

        points = self.kinectPointCloud3DVec[idx].transform(points, T, R)

        return points

    def getPointCloudAll(self):
        pointsAll = []

        for k in xrange(self.kinectNum):
            points = self.getPointCloud(k)
            if points == []:
                continue

            if pointsAll == []:
                pointsAll = points
            else:
                pointsAll = np.vstack((pointsAll, points))

        return pointsAll


    def getRGBImg(self, idx):
        if self.checkIdx(idx) == False:
            return None

        rgbImg = self.kinectRGBImageClientVec[idx].getCurrentImage()
        return rgbImg

    def getRGBImgVec(self):
        imgVec = []
        for k in self.kinectRGBImageClientVec:
            img = k.getCurrentImage()
            imgVec.append(img)

        return imgVec

    def getT(self, idx):
        if self.checkIdx(idx) == False:
            return None

        cTransform = self.kinectCoordinateTransformVec[idx]
        return cTransform.getT()

    def getCoorinateTransform(self, idx):
        if self.checkIdx(idx) == False:
            return None

        return self.kinectCoordinateTransformVec[idx]

    def getCamCoord(self, idx):
        if self.checkIdx(idx) == False:
            return None

        camCoord = self.kinectRGBCamCoordVec[idx]
        return camCoord

    def getAudioDataVec(self):
        if self.kinectAudioClient == None:
            return []

        return self.kinectAudioClient.getAudioData()

    def calcCropCorners(self, idx, wpt, wSize, hSize, zTopMargin = 0.0, angleFixLevel = 1):
        if self.checkIdx(idx) == False:
            return None

        camCoord = self.kinectRGBCamCoordVec[idx]
        rgbImg = self.getRGBImg(idx)

        #trackedDataから、画像座標iPosPixelに変換
        #print "trackedId: " + str(trackedId)
        iPos = camCoord.wPos2iPos(wpt)
        #print "iPos: " + str(iPos)

        iPosPixel = camCoord.iPos2iPosPixel(iPos, rgbImg)
        #print "iPosPixel: " + str(iPosPixel)

        #trackedDataから、人物の画像領域 corner_iPosPixelsを計算
        corner_iPos = camCoord.calcCropImageCoords(wpt,\
                                                    wSize, hSize,\
                                                    zTopMargin, angleFixLevel)

        corner_iPosPixels = []
        for i in xrange(4):
            corner_iPosPixel = camCoord.iPos2iPosPixel(corner_iPos[i], rgbImg)
            corner_iPosPixels.append([corner_iPosPixel[0], corner_iPosPixel[1]])
        #print corner_iPosPixels

        return iPosPixel, corner_iPosPixels

