# -*- coding: utf-8 -*-

import os, sys
import cv2
import numpy as np
import urllib2
from urllib2 import URLError
from urllib2 import HTTPError
import threading
import time

from Util import FXTimeUtil

class HttpGetImage:
    #url: url of image
    #flags: image type (cv2.IMREAD_ANYCOLOR = color image, cv2.CV_LOAD_IMAGE_UNCHANGED = depth 16bit uint

    def __init__(self, url, flags=cv2.IMREAD_ANYCOLOR):
        self.url = url
        self.flags = flags

        self.currentImage = None
        self.fps = 15.0
        self.processThreading = None
        self.threadFlag = False

        self.smp = False #セマフォ

    def getImage(self, readSafe = False):
        r = None
        try:
            r= urllib2.urlopen(self.url)
        except Exception:
            print "getImage error"
            return None

        if r == None:
            return None

        d = r.read()

        img_array = np.asarray(bytearray(d), dtype=np.uint8)
        #img_array = np.frombuffer(d, dtype=dtype)

        #img = cv2.imdecode(img_array, cv2.CV_LOAD_IMAGE_UNCHANGED)
        #img = cv2.imdecode(img_array, cv2.IMREAD_ANYDEPTH)

        if readSafe and self.smp:
            return None

        self.currentImage = cv2.imdecode(img_array, self.flags)

        return self.currentImage

    def getCurrentImage(self):
        if self.currentImage == None:
            return None

        self.smp = True
        img = self.currentImage.copy()
        self.smp = False
        return img

    def _threadProcess(self):
        currentT = 0.
        interval = 1.0/self.fps

        while True:
            if self.threadFlag == False:
                break

            t = FXTimeUtil.getT()
            diffT = t - currentT
            if diffT < interval:
                time.sleep(interval - diffT)

            self.getImage(readSafe=True)

            currentT = t

        print "thread process killed\n"


    def startThread(self, fps=15.0):
        if self.processThreading != None:
            self.stopThread()

        self.fps = fps

        self.processThreading = threading.Thread(target=self._threadProcess)

        self.threadFlag = True
        self.processThreading.start()

    def stopThread(self):
        if self.processThreading == None:
            return

        self.threadFlag = False
        time.sleep(5)
        self.processThreading.join()
        self.processThreading = None

