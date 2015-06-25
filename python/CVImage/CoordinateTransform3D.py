# -*- coding: utf-8 -*-

import os, sys
import cv2
import numpy as np
import math

class CoordinateTransform3D:
    def __init__(self):
         self.R = np.eye(3)
         self.R = self.R.astype(np.float32)
         self.T = np.zeros((3,1), np.float32)

    def dump(self):
        print "T"
        print self.T
        print "R"
        print self.R

    def setT(self, tvec):
        self.T = np.array(tvec)
        self.T = self.T.reshape((3,1))

    def getT(self):
        return self.T.flatten()

    def setR(self, R):
        self.R = R

    def inverse(self):
        invR = np.linalg.inv(self.R)
        invT = invR.dot( self.T )
        invT = -1 * invT

        dst = CoordinateTransform3D()
        dst.setT(invT)
        dst.setR(invR)

        return dst

    def setRvec(self, rvec):
        rvec3 = np.array(rvec)
        rvec3 = rvec3.astype(np.float32)
        self.R, jacobian = cv2.Rodrigues(rvec3)

    def setAxisAngle(self, axisAngle):
        rvec3 = np.zeros(3, np.float32)

        rvec3[0] = axisAngle[0]
        rvec3[1] = axisAngle[1]
        rvec3[2] = axisAngle[2]

        norm = np.linalg.norm(rvec3)
        if norm!=0:
            rvec3 = rvec3/norm

        self.setRvec(rvec3.flatten())

    def setPanTiltRoll(self, pan, tilt, roll):
        p = -pan
        t = -tilt
        r = roll
        p = math.radians(p)
        t = math.radians(t)
        r = math.radians(r)

        cp = math.cos(p)
        sp = math.sin(p)
        ct = math.cos(t)
        st = math.sin(t)
        cr = math.cos(r)
        sr = math.sin(r)

        self.R[0][0] = cr*sp  - cp*sr*st
        self.R[0][1] = -sp*sr - cp*cr*st
        self.R[0][2]  =  cp*ct

        self.R[1][0] = -cp*cr - sp*sr*st
        self.R[1][1]  =  cp*sr - cr*sp*st
        self.R[1][2]  =  ct*sp

        self.R[2][0]  = -ct*sr
        self.R[2][1]  = -cr*ct
        self.R[2][2]  = -st

    def getPanTiltRoll(self):
        m13 = self.R[0][2]
        m33 = self.R[2][2]
        m31 = self.R[2][0]
        m23 = self.R[1][2]
        t = math.asin(self.trigonometricFormat(- m33))
        ct = math.cos(t);
        r = math.asin(self.trigonometricFormat(-m31 / ct));
        p = math.asin(self.trigonometricFormat(m23 / ct));
        cp = m13 / ct
        if cp < 0:
            if p > 0:
                p = math.pi - p
            else:
                p = -math.pi - p

        p = math.degrees(p);
        t = math.degrees(t);
        r = math.degrees(r);
        p = -p
        t = -t
        return p, t, r

    def transform(self, pos):
        pos = np.array(pos)
        pos = pos.reshape((3,1))

        pos = self.R.dot( pos )
        pos = pos + self.T

        return pos.flatten()

    def transformT(self, pos):
        pos = np.array(pos)
        pos = pos.reshape((3,1))

        pos = pos + self.T

        return pos.flatten()

    def transformR(self, pos):
        pos = np.array(pos)
        pos = pos.reshape((3,1))

        pos = self.R.dot( pos )

        return pos.flatten()

    def trigonometricFormat(self, v):
        if v > 1.0:
            return 1.0
        elif v < -1.0:
            return -1.0
        return v