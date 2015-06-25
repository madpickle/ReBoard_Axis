# -*- coding: utf-8 -*-

import os, sys
import cv2
import numpy as np
import json
import time
import threading

from CVImage import HttpGetImage
from CVImage import InternalCalib
from CVImage import FXImageUtil
from Util import FXTimeUtil


#use royweb for visualize parameters
useRoyWeb = False
if useRoyWeb:
    from royweb.networking import PacketHandler
    ps = PacketHandler("127.0.0.1", 9999)


class WhiteBoardClient:
    def __init__(self, paramFile):
        #load parameter file
        f = open(paramFile)
        self.param = json.load(f)
        f.close()

        self.movementCheckImg = None
        self.diffCheckImg = None
        self.diffCheckMask = None

        self.thumbScale = 1.0

        self.movementVal = 0.0
        self.movementValMean = 0.0

        self.debugLevel = 0
        if self.param.has_key('debugLevel'):
            self.debugLevel = self.param['debugLevel']

        self.movementCheckThread = None

        self.init()

    #initialize parameters for undistort and cropping
    def init(self):
        #init params for HD diff check image
        self.imgClient = HttpGetImage.HttpGetImage(self.param['url'])
        self.intrCalib = InternalCalib.InternalCalib(self.param['internalParamFile'],\
                                                    self.param['size'])

        srcSize = self.param['size']
        dstSize = self.param['dstImage']['size']
        self.cropM = self.calcCropMatrix(srcSize, dstSize)

        # create mask image
        imgShape = (dstSize[1], dstSize[0])
        self.diffCheckMask = np.zeros(imgShape, dtype=np.uint8)
        maskScale = 0.9 # use 90% of area for detecting difference
        maskMin = (1.0 - maskScale) * 0.5
        maskMax = 1.0 - maskMin
        self.diffCheckMask[int(dstSize[1] * maskMin):int(dstSize[1] * maskMax), int(dstSize[0] * maskMin):int(dstSize[0] * maskMax)]\
            = 255
        cv2.imwrite("maskImg.png", self.diffCheckMask) # for debug

        thumbSize = self.param['dstThumb']['size']
        self.thumbScale = float(thumbSize[0])/float(dstSize[0])

        self.thumbRectFlag = False
        if self.param['dstThumb'].has_key('rect'):
            rect = self.param['dstThumb']['rect']
            self.thumbRectFlag = True

            self.thumbRectThickness = rect['thickness']
            c = rect['color']
            self.thumbRectColor = (c[2], c[1], c[0])

        #init params for Low Res movement check image
        self.moveCheckImgClient = HttpGetImage.HttpGetImage(self.param['movementCheck']['url'])
        self.moveCheckIntrCalib = InternalCalib.InternalCalib(self.param['internalParamFile'],\
                                                              self.param['movementCheck']['size'])

        srcSize = self.param['movementCheck']['size']
        dstSize = self.param['movementCheck']['processSize']
        self.cropMoveCheckM = self.calcCropMatrix(srcSize, dstSize)


    def calcCropMatrix(self, srcSize, dstSize):
        crop = self.param['crop']
        srcCropRect = [[crop['topLeft'][0] * srcSize[0], crop['topLeft'][1] * srcSize[1]],\
                       [crop['btmLeft'][0] * srcSize[0], crop['btmLeft'][1] * srcSize[1]],\
                       [crop['btmRight'][0] * srcSize[0], crop['btmRight'][1] * srcSize[1]],\
                       [crop['topRight'][0] * srcSize[0], crop['topRight'][1] * srcSize[1]]]
        srcCropRect = np.array(srcCropRect).astype(np.float32)

        dstCropRect = [[0.0, 0.0],\
                       [0.0, dstSize[1]],\
                       [dstSize[0], dstSize[1]],\
                       [dstSize[0], 0.0]]
        dstCropRect = np.array(dstCropRect).astype(np.float32)

        M = cv2.getPerspectiveTransform(srcCropRect, dstCropRect)
        return M

    #get whiteboard image
    def getImg(self):
        img = self.imgClient.getImage()
        if img == None:
            return None

        img = self.intrCalib.undistort(img)

        dstSize = self.param['dstImage']['size']
        dstSize = (dstSize[0], dstSize[1])
        img = cv2.warpPerspective(img, self.cropM, dstSize)

        return img

    #get low resolution image for movement check
    def getMovementCheckImg(self):
        img = self.moveCheckImgClient.getImage()
        if img == None:
            return None

        img = self.moveCheckIntrCalib.undistort(img)

        dstSize = self.param['movementCheck']['processSize']
        dstSize = (dstSize[0], dstSize[1])
        img = cv2.warpPerspective(img, self.cropMoveCheckM, dstSize)

        return img

    # movement check process
    def movementCheckProcess(self):
        interval = self.param['movementCheck']['interval']


        while True:
            sTime = FXTimeUtil.getT()

            img = self.getMovementCheckImg()
            if img==None:
                continue

            imgGray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            if self.movementCheckImg == None:
                self.movementCheckImg = imgGray

            diffImg = cv2.absdiff(imgGray, self.movementCheckImg)
            val = cv2.mean(diffImg)
            val = float(val[0])

            duration = FXTimeUtil.getT() - sTime

            if duration < interval:
                time.sleep(interval - duration)
                duration = interval

            self.movementVal = val

            w = duration/1.0
            w = min(w, 1.0)
            self.movementValMean = w * val + (1.0-w) * self.movementValMean

            self.movementCheckImg = imgGray

            if self.debugLevel >= 3:
                print "movement: %f (mean %f)" % (self.movementVal, self.movementValMean)

            if useRoyWeb:
                ps.send('movement', self.movementVal, 'v', 'movementVal')
                ps.send('movementMean', self.movementValMean, 'v', 'movementValMean')


    def startMovementCheckThread(self):
        self.movementCheckThread = threading.Thread(target=self.movementCheckProcess)
        self.movementCheckThread.start()

    def stopMovementCheckThread(self):
        if self.movementCheckThread == None:
            return

        self.movementCheckThread.join()
        self.movementCheckThread = None

    def diffCheckProcess(self):
        interval = self.param['interval']

        while True:
            sTime = FXTimeUtil.getT()

            if self.movementValMean < self.param['movementCheck']['thr']:
                if self.debugLevel >= 2:
                    print "no movements. diff check"

                img = self.getImg()
                if img==None:
                    continue

                imgGray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                imgGray = cv2.GaussianBlur(imgGray, (5,5),0)

                lapImg = cv2.Laplacian(imgGray, cv2.CV_32F, ksize=3)






                #lapImg = lapImg.astype(np.uint8)

                #conjunction
                #kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                #lapImg = cv2.dilate(lapImg, kernel, iterations=2)
                #lapImg = cv2.erode(lapImg, kernel, iterations=2)

                if self.diffCheckImg == None:
                    self.diffCheckImg = lapImg

                diffImg = cv2.absdiff(lapImg, self.diffCheckImg)
                ret, diffImg = cv2.threshold(diffImg, 10, 255, cv2.THRESH_BINARY)
                diffImg = diffImg.astype(np.uint8)

                #noise reduction
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                diffImg = cv2.erode(diffImg, kernel, iterations=2)
                diffImg = cv2.dilate(diffImg, kernel, iterations=2)

                diffImg = cv2.bitwise_and(diffImg, self.diffCheckMask)

                if self.debugLevel >= 1:
                    dispImg = diffImg.copy()
                    dispImg = FXImageUtil.scaleImage(diffImg, 0.25)
                    cv2.imshow("diffImg", dispImg)

                val = cv2.mean(diffImg)
                val = float(val[0])

                self.diffVal = val

                self.diffCheckImg = lapImg

                if self.debugLevel >= 2:
                    print "HD difference val: %f" % self.diffVal

                if useRoyWeb:
                    ps.send('diff', self.diffVal, 'v', 'diffVal')

                if self.diffVal > self.param['thr']:
                    print "difference is detected"

                    thumbSize = self.param['dstThumb']['size']
                    thumbImg = cv2.resize(img, (thumbSize[0], thumbSize[1]))

                    if self.thumbRectFlag:
                        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (100, 100))
                        diffImgArea = cv2.dilate(diffImg, kernel)
                        diffImgArea = cv2.erode(diffImgArea, kernel)

                        contours, hierarchy = cv2.findContours(diffImgArea, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

                        #get max rectangle
                        areas = [cv2.contourArea(contour) for contour in contours]
                        cnt_max = [contours[areas.index(max(areas))]][0]
                        rect = cv2.boundingRect(cnt_max)

                        #draw rectangle
                        offset = 20
                        pt1 = (int((rect[0]-offset) * self.thumbScale), int((rect[1]-offset) * self.thumbScale))
                        pt2 = (int((rect[0]+rect[2]+offset) * self.thumbScale), int((rect[1]+rect[3]+offset) * self.thumbScale))
                        cv2.rectangle(thumbImg, pt1, pt2, self.thumbRectColor, thickness=self.thumbRectThickness)


                    self.handleWBCapture(img, thumbImg)



                    if self.debugLevel >= 1:
                        dispImg = FXImageUtil.scaleImage(img, 0.25)
                        cv2.imshow("captured wb", dispImg)
                        dispImg = FXImageUtil.scaleImage(diffImg, 0.25)
                        cv2.imshow("captured wb diff", dispImg)

            else:
                if self.debugLevel >= 2:
                    print "movement is detected. skip diff check"


            duration = FXTimeUtil.getT() - sTime

            if duration < interval:
                time.sleep(interval - duration)
                duration = interval

            cv2.waitKey(1)

    # do something to the captured whiteboard image!
    def handleWBCapture(self, img, thumbImg):
        t = FXTimeUtil.getT()
        dtString = FXTimeUtil.T2DateString(t)
        filename = dtString + ".jpg"
        cv2.imwrite(filename, img)

        filename = dtString + "_thumb.jpg"
        cv2.imwrite(filename, thumbImg)