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
from Util import FXTimeUtil
from MessageBoard import MessageBoard

class KinectAudioMBClientHandler(MessageBoard.SimpleMessageHandler):
    def __init__(self, kinectAudioMBClient, idx):
        MessageBoard.SimpleMessageHandler.__init__(self)
        self.kinectAudioMBClient = kinectAudioMBClient
        self.idx = idx

    def handleMessage(self, msg):
        #print msg
        self.kinectAudioMBClient.onReceive(msg, self.idx)

class KinectAudioClient:
    def __init__(self, msgPatternVec, host=MessageBoard.DEFAULT_MESSAGE_BOARD_HOST, port=MessageBoard.MESSAGE_BOARD_PORT):
        self.mbClient = None

        if host == None:
            return
        self.mbClient = MessageBoard.MessageClient(host, port)

        self.msgPatternVec = msgPatternVec
        s = len(self.msgPatternVec)
        self.audioDataVec = [None]*s

        for i in xrange(s):
            handler = None
            pattern = self.msgPatternVec[i]
            if pattern:
                self.mbClient.registerMessageHandler(KinectAudioMBClientHandler(self, i), pattern)

        self.mbClient.listenForeverInThread()

    def onReceive(self, msg, idx):
        self.audioDataVec[idx] = msg

    def getAudioData(self):
        return self.audioDataVec





