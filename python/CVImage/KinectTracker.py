# -*- coding: utf-8 -*-

import os, sys
import cv2
import numpy as np
import math
import json
import threading
import time

sys.path.append('../')

from CVImage import FXImageUtil
from CVImage import KinectClient
from CVImage import D3DFloorMap
from CVImage import CoordinateTransform3D
from CVImage import PointCloud3D
from Face import DetectOrientation
from Util import FXTimeUtil
from MessageBoard import MessageBoard

class KinectTracker():
    def __init__(self, kinectClient, trackInfoJsonPath = "trackInfo_default.json"):
        self.kinectClient = kinectClient

        self.trackInfo = {}

        self.loadTrackInfo(trackInfoJsonPath)

        viewPort = self.trackInfo['viewPort']
        self.floorMapSize = (int((viewPort['x']['max'] - viewPort['x']['min'])/self.trackInfo['pixel2mm']), \
                             int((viewPort['y']['max'] - viewPort['y']['min'])/self.trackInfo['pixel2mm']))
        pixel2mm = self.trackInfo['pixel2mm']

        self.kinectFloorMap = D3DFloorMap.D3DFloorMap(viewPort, pixel2mm)

        mbHost = None
        if self.trackInfo.has_key('messageBoardHost'):
            mbHost = self.trackInfo['messageBoardHost']
        mbPort = MessageBoard.MESSAGE_BOARD_PORT
        if self.trackInfo.has_key('messageBoardPort'):
            mbPort = self.trackInfo['messageBoardPort']

        self.useFaceDetection = False
        if self.trackInfo.has_key("face"):
            self.useFaceDetection = True
            self.faceCropParams = self.trackInfo['face']['crop']

        self.detectOrientation = DetectOrientation.DetectOrientation("./classifiers")
        self.currentFaceAngleImg = None #faceAngleImg
        self.currentFaceAngleSumImg = None #faceAngleImgの加算画像
        self.currentFaceAngleProcessTime = 0 #前回の処理時間
        self.faceAngleConfMax = 0 #最大値 (画像化のため)


        self.currentTrackedData = {} #現在のtrackedData
        self.currentTrackedDataFace = {} #顔向き付きのtrackedData

        self.currentTrackedId = 0 #新しく付けるID　だんだん増える

        self.processThreading = None #trackingのprocess thread
        self.processThreadingFace = None #face detectionのprocess thread
        self.threadFlag = False

        self.currentAudioAngleImg = None #audioAngleImg
        self.currentAudioAngleSumImg = None #autioAngleの加算画像
        self.currentAudioProcessTime = 0 #前回の処理時刻


    def _threadProcess(self):
        while True:
            if self.threadFlag == False:
                break

            self.trackProcess()
            cv2.waitKey(1)

        print "thread process killed\n"

    def _threadProcessFace(self):
        while True:
            if self.threadFlag == False:
                break

            self.faceProcess()

            cv2.waitKey(1)

        print "thread process killed [face]\n"


    def startThread(self):
        if self.processThreading != None:
            self.stopThread()

        self.processThreading = threading.Thread(target=self._threadProcess)
        if self.useFaceDetection:
            self.processThreadingFace = threading.Thread(target=self._threadProcessFace)

        self.threadFlag = True
        self.processThreading.start()
        if self.processThreadingFace:
            self.processThreadingFace.start()

    def stopThread(self):
        if self.processThreading == None:
            return

        self.threadFlag = False
        time.sleep(5)
        self.processThreading.join()
        self.processThreading = None

        if self.processThreadingFace:
            self.processThreadingFace.join()
            self.processThreadingFace = None

    def loadTrackInfo(self, trackInfoJsonPath):
        f = open(trackInfoJsonPath, 'r')
        self.trackInfo = json.load(f)
        f.close()

    def getFloorImage(self):
        points = self.kinectClient.getPointCloudAll()

        viewPort = self.kinectFloorMap.viewPort
        pixel2mm = self.kinectFloorMap.pixel2mm

        pc3D = PointCloud3D.PointCloud3D()

        #st = FXTimeUtil.getT()

        floorImg = pc3D.convertToImage(points, \
            [viewPort['x']['min'], viewPort['x']['max']],\
            [viewPort['y']['min'], viewPort['y']['max']],\
            [viewPort['z']['min'], viewPort['z']['max']],\
            pixel2mm,\
            PointCloud3D.CVTIMAGE_USE_MAX)

        #et = FXTimeUtil.getT()
        #print et-st


        floorImg = cv2.flip(floorImg, flipCode=0)#上下反転
        return floorImg

    def getAudioMapImg(self):
        audioAngleImgTotal = self.kinectFloorMap.getBlankImg(dtype=np.uint16)

        audioDataVec = self.kinectClient.getAudioDataVec()

        for k in xrange(self.kinectClient.getKinectNum()):
            audioData = audioDataVec[k]
            if audioData == None:
                continue

            sourceAngle = audioData['sourceAngle']
            sourceConfidence = audioData['sourceConfidence']

            if sourceConfidence == 0:
                continue

            kinect_wPos = np.array(self.kinectClient.getT(k))
            kinect_cTransform = self.kinectClient.getCoorinateTransform(k)

            distance = 10000. #10(m)
            audioDirPos = [math.tan(math.radians(- sourceAngle))*distance, 0., distance]
            audioDirPos = kinect_cTransform.transformR(audioDirPos)

            audioDst_wPos = kinect_wPos + np.array(audioDirPos)

            kinect_mPos = self.kinectFloorMap.wPos2mapPos(kinect_wPos)
            audioDst_mPos = self.kinectFloorMap.wPos2mapPos(audioDst_wPos)

            audioAngleImg = self.kinectFloorMap.getBlankImg(dtype=np.uint8)

            val = int(255. * sourceConfidence) #最大255
            #val = sourceConfidence
            if val == 0:
                continue

            minRangeAngle = 10.
            rangeAngle = minRangeAngle + (90. - minRangeAngle) * (1.0-sourceConfidence) #minRangeAngle-90度。confidence==1で20度

            audioAngleImg = FXImageUtil.drawSensingDirection(audioAngleImg, kinect_mPos, audioDst_mPos,\
                                                             rangeAngle, val)
            audioAngleImgTotal = audioAngleImgTotal + audioAngleImg

        audioAngleImgTotal = audioAngleImgTotal / self.kinectClient.getKinectNum() #kinect台数で割る
        audioAngleImgTotal = audioAngleImgTotal.astype(np.uint8)
        return audioAngleImgTotal


    def trackProcess(self):
        t = FXTimeUtil.getT()
        floorImg = self.getFloorImage()
        if floorImg == None:
            return

        viewPort = self.trackInfo['viewPort']
        floorImg8UC3, floorImgBin = FXImageUtil.createColorMap(floorImg, 0., viewPort['z']['max'])

        noiseReduction = self.trackInfo['noiseReduction']
        if noiseReduction > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (noiseReduction, noiseReduction))
            floorImgBin = cv2.morphologyEx(floorImgBin, cv2.MORPH_OPEN, kernel)
            floorImgBin = cv2.morphologyEx(floorImgBin, cv2.MORPH_CLOSE, kernel)

        binDilate = self.trackInfo['binDilate']
        if binDilate > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (binDilate, binDilate))
            floorImgBin = cv2.dilate(floorImgBin, kernel)
        binErode = self.trackInfo['binErode']
        if binErode > 0:
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (binErode, binErode))
            floorImgBin = cv2.erode(floorImgBin, kernel)

        floorImgBinOrig = floorImgBin.copy()

        contours, hierarchy = cv2.findContours(floorImgBin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        gaussianSize = self.trackInfo['gaussianSize']
        if gaussianSize > 0:
            floorImgGaussian = cv2.GaussianBlur(floorImg,(gaussianSize,gaussianSize),0)
        else:
            floorImgGaussian = floorImg.copy()

        #floorImg = floorImgGaussian
        #floorImgGaussian8UC3 = FXImageUtil.createColorMap(floorImgGaussian, 0., viewPort['z']['max'])[0]
        #cv2.imshow("floorImgGaussian", floorImgGaussian8UC3)


        ######## audioのマップを作成する
        self.audioProcess()

        ########トラッキング処理
        trackedData = {'dataId': 'kinectTracker', 't': t}

        points = []

        for contour in contours:
            if len(contour) < 5:
                continue #too small

            box = cv2.fitEllipse(contour)

            #検出したサイズをmmに (minSize, maxSize)
            objectSizeMM = (min(box[1]) * self.trackInfo['pixel2mm'], max(box[1]) * self.trackInfo['pixel2mm'])
            #print objectSize

            #サイズのチェック
            if objectSizeMM[0] < self.trackInfo['objectSize']['min']: #小さい方の大きさ
                continue
            if objectSizeMM[1] > self.trackInfo['objectSize']['max']: #大きい方の大きさ
                continue

            ellipseImgBin = np.zeros(floorImgBin.shape).astype(np.uint8)
            cv2.ellipse(ellipseImgBin, box, (255), -1)
            minMaxLoc = cv2.minMaxLoc(floorImgGaussian, mask=ellipseImgBin)

            #人物のシルエット
            personBinImg = floorImgBin * ellipseImgBin

            #人物のシルエットの面積/楕円の面積
            areaSize_ellipse = np.count_nonzero(ellipseImgBin)
            areaSize_personBin = np.count_nonzero(personBinImg)
            areaSizeRate = 0.
            if areaSize_ellipse > 0:
                areaSizeRate = float(areaSize_personBin) / float(areaSize_ellipse)


            #print box #((centerx, centery), (w,h), angle?)
            boxCenter = box[0]

            object_height = int(minMaxLoc[1])
            maxLoc = minMaxLoc[3]
            object_mPos = [maxLoc[0], maxLoc[1]]
            #object_mPos = [int(boxCenter[0]), int(boxCenter[1])]

            object_wPos = self.kinectFloorMap.mapPos2wPos(object_mPos, object_height)

            audioScore = 0.
            if self.currentAudioAngleSumImg != None:
                audioScore = float(self.currentAudioAngleSumImg[object_mPos[1]][object_mPos[0]])

            tData = {}
            tData['x'] = object_wPos[0]
            tData['y'] = object_wPos[1]
            tData['z'] = object_wPos[2]
            tData['width'] = objectSizeMM[1] #大きい方
            tData['height'] = objectSizeMM[0] #小さい方

            mData = {}
            mData['x'] = object_mPos[0]
            mData['y'] = object_mPos[1]
            mData['box'] = box
            mData['areaSizeRate'] = areaSizeRate

            audioData = {}
            audioData['score'] = audioScore

            #print areaSizeRate

            point = {'trackedData': tData, 'trackedMapData': mData, 'audio': audioData}
            points.append(point)


        trackedData['data'] = points

        self.putTrackedIds(self.currentTrackedData, trackedData)


        ###### visualize

        audioAngleSumImg8UC3 = cv2.cvtColor(self.currentAudioAngleSumImg, cv2.COLOR_GRAY2BGR)
        floorImgBin8UC3 = cv2.cvtColor(floorImgBinOrig, cv2.COLOR_GRAY2BGR)

        #floorImg8UC3に描画
        if trackedData.has_key('data'):
            points = trackedData['data']
            for point in points:
                mPos = [point['trackedMapData']['x'], point['trackedMapData']['y']]
                box = point['trackedMapData']['box']

                cv2.ellipse(floorImg8UC3, box, (0, 0, 255), 1)
                cv2.circle(floorImg8UC3, (mPos[0], mPos[1]), 3, (0,0,255), -1)
                trackStr = "(" + point['trackedId'] + ")" + str(object_wPos[2])
                cv2.putText(floorImg8UC3, trackStr, (mPos[0]+5, mPos[1]), cv2.FONT_HERSHEY_PLAIN, 0.8, (0,0,255))

                #cv2.ellipse(audioAngleSumImg8UC3, box, (0, 0, 255), 1)
                cv2.circle(audioAngleSumImg8UC3, (mPos[0], mPos[1]), 3, (0,0,255), -1)

                cv2.ellipse(floorImgBin8UC3, box, (0, 0, 255), 1)
                cv2.circle(floorImgBin8UC3, (mPos[0], mPos[1]), 3, (0,0,255), -1)


        cv2.imshow("floorImg", floorImg8UC3)
        cv2.imshow("audioAngleImg", audioAngleSumImg8UC3)
        cv2.imshow("floorImgBin", floorImgBin8UC3)


        self.currentTrackedData = trackedData
        #print self.currentTrackedData


    def getTrackedData(self):
        return self.currentTrackedData

    def getTrackedDataFace(self):
        return self.currentTrackedDataFace

    def audioProcess(self):
        t = FXTimeUtil.getT()

        audioAngleImg = self.getAudioMapImg()

        self.currentAudioAngleImg = audioAngleImg
        if self.currentAudioAngleSumImg == None:
            self.currentAudioAngleSumImg = self.currentAudioAngleImg.copy()
        else:
            processInterval = t - self.currentAudioProcessTime
            timeRange = 1.0
            processInterval = min (processInterval, timeRange)
            w = processInterval / timeRange

            self.currentAudioAngleSumImg = cv2.addWeighted(self.currentAudioAngleSumImg, (1.0 - w),\
                                                           self.currentAudioAngleImg, w, 0)

        self.currentAudioProcessTime = t

    def faceProcess(self):
        trackedData = self.getTrackedData()

        if trackedData.has_key('data') == False:
            return

        t = trackedData['t']
        points = trackedData['data']
        rgbImgVec = self.kinectClient.getRGBImgVec()

        faceAngleImg = self.kinectFloorMap.getBlankImg(dtype=np.uint16)


        ####### only one kinect (so far)
        kinectIdx = 0

        rgbImgOrig = rgbImgVec[kinectIdx]
        if rgbImgOrig == None:
            return

        rgbImg = rgbImgOrig.copy()
        camCoord = self.kinectClient.kinectRGBCamCoordVec[kinectIdx]

        croppedImgs = []
        mPosVec = []

        totalConf = 0

        for point in points:
            p = point['trackedData']
            wPos = [p['x'], p['y'], p['z']]
            trackedId = point['trackedId']

            rt = self.kinectClient.calcCropCorners(kinectIdx,\
                                                   wPos,\
                                                   self.faceCropParams['width'], self.faceCropParams['height'],\
                                                   self.faceCropParams['zTopMergin'], self.faceCropParams['cropType'])
            if rt == None:
                continue

            iPosPixel, corner_iPosPixels = rt

            cv2.circle(rgbImg, (iPosPixel[0], iPosPixel[1]), 6, (0, 0, 255), -1)
            cv2.putText(rgbImg, str(trackedId), (iPosPixel[0]+7, iPosPixel[1]), cv2.FONT_HERSHEY_PLAIN, 2.0, (0,0,255))

            cv2.polylines(rgbImg, np.array([corner_iPosPixels]), True, (0,255,0), 2)

            #人物領域をcroppedImgとして抜出
            cropImgSize = (50, 70) #[width, height] pixels
            croppedImg = FXImageUtil.cropImage(rgbImgOrig, corner_iPosPixels, (140, 100))

            minSize = int(min(cropImgSize)*0.2)
            maxSize = int(max(cropImgSize)*0.8)
            detAng, detConf = self.detectOrientation.detect(croppedImg, minSize, maxSize)


            detAngDeg = math.degrees(detAng)

            camDir = np.array(self.kinectClient.getT(kinectIdx)) - np.array(wPos)
            camDir[2] = 0
            faceCoord = CoordinateTransform3D.CoordinateTransform3D()
            #一般的な場合、なぜか(-90, 90, 0)がR=eyeになる。なので、その相対。detAngDegは時計回りに正
            facePan = -90 + detAngDeg

            faceCoord.setPanTiltRoll(facePan, 90, 0)
            faceDir = faceCoord.transformR(camDir)
            faceDir = faceDir/np.linalg.norm(faceDir)
            faceDirWPos = np.array(wPos) + faceDir * 500.0
            faceDirIPos = camCoord.wPos2iPos(faceDirWPos)
            faceDirIPosPixels = camCoord.iPos2iPosPixel(faceDirIPos, rgbImg)

            if detConf > 10:
                angText = "ang:%.0f, conf:%.0f" % (detAngDeg, detConf)
                cv2.putText(rgbImg, angText, (iPosPixel[0]+7, iPosPixel[1]+30), cv2.FONT_HERSHEY_PLAIN, 1.5, (0,0,255))
                cv2.line(rgbImg,  (iPosPixel[0], iPosPixel[1]), (faceDirIPosPixels[0], faceDirIPosPixels[1]), (0,255,255), 3)

            #trackedDataに'face'情報を追加
            faceData = {}
            faceData['angle'] = detAng
            faceData['confidence'] = detConf
            point['face'] = faceData

            mPos = self.kinectFloorMap.wPos2mapPos(wPos)
            mPosVec.append(mPos)
            if detConf > 0:
                faceDirWPos2 = np.array(wPos) + faceDir*10000.
                faceDir_mPos = self.kinectFloorMap.wPos2mapPos(faceDirWPos2)
                faceAngleImg_person = self.kinectFloorMap.getBlankImg(dtype=np.uint16)
                rangeAngle = 30. #degrees
                val = detConf
                faceAngleImg_person = FXImageUtil.drawSensingDirection(faceAngleImg_person, mPos, faceDir_mPos,\
                                                                       rangeAngle, val)
                faceAngleImg = faceAngleImg + faceAngleImg_person

            totalConf = totalConf + detConf


            #表示用にcroppedImgsに横につなげる
            if np.alen(croppedImgs) > 0:
                croppedImgs = np.hstack((croppedImgs, croppedImg))
            else:
                croppedImgs = np.copy(croppedImg)

        self.currentTrackedDataFace = trackedData


        dispImg = cv2.resize(rgbImg, (810, 540))
        #dispImg = rgbImg

        cv2.imshow("rgbFace", dispImg)
        #cv2.imshow("croppedImgs", croppedImgs)


        self.currentFaceAngleImg = faceAngleImg

        if self.currentFaceAngleSumImg == None:
            self.currentFaceAngleSumImg = self.currentFaceAngleImg.copy()
        else:
            processInterval = t - self.currentFaceProcessTime
            timeRange = 1.0
            processInterval = min (processInterval, timeRange)
            w = processInterval / timeRange

            self.currentFaceAngleSumImg = cv2.addWeighted(self.currentFaceAngleSumImg, (1.0 - w),\
                                                           self.currentFaceAngleImg, w, 0)

        self.faceAngleConfMax = max(self.faceAngleConfMax, totalConf)
        self.currentFaceProcessTime = t

        #表示系
        self.faceAngleConfMax = max(self.faceAngleConfMax, totalConf)
        if self.faceAngleConfMax > 0:
            faceAngleImg8UC3 = FXImageUtil.createColorMap(self.currentFaceAngleSumImg, 0.0, self.faceAngleConfMax)[0]
            #faceAngleImg8UC3 = FXImageUtil.createColorMap(self.currentFaceAngleImg, 0.0, self.faceAngleConfMax)[0]

            for mPos in mPosVec:
                cv2.circle(faceAngleImg8UC3, (int(mPos[0]), int(mPos[1])), 3, (0, 0, 255), -1)

            cv2.imshow("faceAngleImg", faceAngleImg8UC3)


    #nextTrackDataにtrackedIdをつける
    #   currentTrackData:　現在のデータ
    #   nextTrackData: 次のデータ
    def putTrackedIds(self, currentTrackData, nextTrackData):
        if nextTrackData.has_key('data') == False:
            return
        nPoints = nextTrackData['data']
        if len(nPoints) == 0:
            return

        trackBoxMerginPixels = self.trackInfo['trackBoxMergin']/self.trackInfo['pixel2mm']

        if currentTrackData.has_key('data'):
            cPoints = currentTrackData['data']
            for cPoint in cPoints:
                cwPos = [cPoint['trackedData']['x'],\
                         cPoint['trackedData']['y'],\
                         cPoint['trackedData']['z']]
                cwPos = np.array(cwPos)
                distVec = []
                nwPosVec = []

                for nPoint in nPoints:
                    nwPos = [nPoint['trackedData']['x'],\
                             nPoint['trackedData']['y'],\
                             nPoint['trackedData']['z']]
                    nwPos = np.array(nwPos)
                    distVec.append(np.linalg.norm(nwPos-cwPos))
                    nwPosVec.append(nwPos)
                minIdx = np.argmin(distVec)

                #cPointとの距離が最少のnPointを取得
                nPoint = nPoints[minIdx]
                if nPoint.has_key('trackedId'):
                    continue #既に割り振られていれば、このtrackedIdは死ぬ(????)

                #cPointのboxの中に入っているかをチェック
                box = cPoint['trackedMapData']['box']
                boxImg = np.zeros((self.floorMapSize[1], self.floorMapSize[0]), dtype=np.uint8)
                box = (box[0], (box[1][0] + trackBoxMerginPixels, box[1][1] + trackBoxMerginPixels), box[2])

                cv2.ellipse(boxImg, box, 255, -1)
                nmPos = [nPoint['trackedMapData']['x'], nPoint['trackedMapData']['y']]

                if boxImg[nmPos[1]][nmPos[0]] > 0:
                    nPoint['trackedId'] = cPoint['trackedId']

        for nPoint in nPoints:
            if nPoint.has_key('trackedId'):
                continue
            nPoint['trackedId'] = str(self.currentTrackedId)
            self.currentTrackedId = self.currentTrackedId + 1







################################## OLD Codes

    def getClosestTrackedIdByDist(self, target_wPos, t = 0):
        if self.currentTrackedData.has_key('t') == False:
            return None

        targetPos = np.array(target_wPos[:2])
        points = self.currentTrackedData['data']

        distVec = []
        for point in points:
            pos = np.array([point['trackedData']['x'], point['trackedData']['y']])
            distVec.append(np.linalg.norm(pos-targetPos))

        if len(distVec) == 0:
            return None


        distVec = np.array(distVec)

        minIdx = np.argmin(distVec)
        minVal = distVec[minIdx]

        t_diff = 0
        if t > 0:
            t_diff = t - self.currentTrackedData['t']
        if t_diff > 0:
            minVal = minVal / t_diff

        if minVal<self.trackInfo['trackSpeedThr']:
            return points[minIdx]['trackedId']

        return None

    def getClosestTrackedIdByBox(self, target_mPos):
        if self.currentTrackedData.has_key('t') == False:
            return None

        trackBoxMerginPixels = self.trackInfo['trackBoxMergin']/self.trackInfo['pixel2mm']

        points = self.currentTrackedData['data']

        for point in points:
            box = point['trackedMapData']['box']
            boxImg = np.zeros((self.floorMapSize[1], self.floorMapSize[0]), dtype=np.uint8)
            box = (box[0], (box[1][0] + trackBoxMerginPixels, box[1][1] + trackBoxMerginPixels), box[2])

            cv2.ellipse(boxImg, box, 255, -1)
            if boxImg[target_mPos[1]][target_mPos[0]] > 0:
                return point['trackedId']

        return None

