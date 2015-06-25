# -*- coding: utf-8 -*-

import os, sys
import cv2
import numpy as np
import math
import json
import time

sys.path.append('../')

# 3Dデータから、マップ座標の画像を生成する
# 主に、KinectTrackingで利用

PIXEL2MM_DEFAULT = 20.0

class D3DFloorMap():
    # viewPort: {'x': {'min', 'max}}, 'y': {'min', 'max'}, 'z': {'min', 'max'}}
    # pixel2mm: 1 pixel == ? mm
    def __init__(self, viewPort=None, pixel2mm=PIXEL2MM_DEFAULT):
        self.viewPort = {'x': {'min': 0.0, 'max': 10000.0}, 'y': {'min': 0.0, 'max': 10000.0}}
        self.pixel2mm = PIXEL2MM_DEFAULT

        self.init(viewPort, pixel2mm)

    def init(self, viewPort=None, pixel2mm=PIXEL2MM_DEFAULT):
        if viewPort != None:
            self.viewPort = viewPort
        self.pixel2mm = pixel2mm

        self.mapSize = (int((self.viewPort['x']['max'] - self.viewPort['x']['min'])/self.pixel2mm), \
                        int((self.viewPort['y']['max'] - self.viewPort['y']['min'])/self.pixel2mm))

    def loadConfig(self, file):
        config = json.load(file)

        viewPort = None
        if config.has_key('viewPort'):
            viewPort = config['viewPort']

        pixel2mm = PIXEL2MM_DEFAULT
        if config.has_key('pixel2mm'):
            pixel2mm = config['pixel2mm']

        self.init(viewPort, pixel2mm)


    def mapPos2wPos(self, mPos, height):
        wPos = [mPos[0]*self.pixel2mm, \
                (self.mapSize[1]-mPos[1])*self.pixel2mm, \
                height]

        wPos[0] = wPos[0] + self.viewPort['x']['min']
        wPos[1] = wPos[1] + self.viewPort['y']['min']

        return wPos

    def wPos2mapPos(self, wPos):
        mPos = [(wPos[0] - self.viewPort['x']['min'])/self.pixel2mm,\
                (wPos[1] - self.viewPort['y']['min'])/self.pixel2mm ]
        mPos[1] = self.mapSize[1] - mPos[1]

        return mPos

    def getBlankImg(self, dtype=np.uint8):
        img = np.zeros((self.mapSize[1], self.mapSize[0]), dtype=dtype)
        return img
