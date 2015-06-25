# -*- coding: utf-8 -*-

import os,sys
import cv2
import numpy as np
import math

NOIMAGE = []

def imageInfoStr(srcImg):
    rtStr = "shape: " + str(srcImg.shape) + ", dtype: " + str(srcImg.dtype)
    return rtStr

def color2gray8UC3(srcImg):
    grayImg = cv2.cvtColor(srcImg, cv2.COLOR_RGB2GRAY)

    srcImgVec = [grayImg, grayImg, grayImg]
    dstImg = cv2.merge(srcImgVec)

    return dstImg

#srcImg:
#return: dstImg, maskImg
#   dstImg: color map image
#   maskImg: mask image of color map (more than 0.0)
def createColorMap(srcImg, min=0.0, max=0.0):
    dstImg8U = (srcImg-min) * (255./(max-min))

    dstImg8U = dstImg8U.astype(np.uint8)
    colorMapImg = cv2.applyColorMap(dstImg8U, cv2.COLORMAP_JET)

    srcImg32f = srcImg.astype(np.float32)
    retVal, maskImg = cv2.threshold(srcImg32f, min, 255, cv2.THRESH_BINARY)
    maskImg = maskImg.astype(np.uint8)

    return colorMapImg, maskImg


def copyMask(srcImg0, srcImg1, maskImg):
    invMaskImg = cv2.bitwise_not(maskImg)

    dstImg = cv2.bitwise_and(srcImg0, srcImg0, mask=invMaskImg)

    dstImg = cv2.add(dstImg, srcImg1, dstImg, mask=maskImg)

    return dstImg

# srcImgを、srcRect[[x,y], ...]の部分を切り抜いてdstSize (width, height)にする
def cropImage(srcImg, srcRect, dstSize):
    if srcImg == None:
        return None

    dst_aspect = float(dstSize[1])/float(dstSize[0])



    srcRect = np.array(srcRect).astype(np.float32)

    dstRect = [[0, 0],\
               [0, dstSize[1]],\
               [dstSize[0], dstSize[1]],\
               [dstSize[0], 0]]
    dstRect = np.array(dstRect).astype(np.float32)


    M = cv2.getPerspectiveTransform(srcRect, dstRect)

    dstImg = cv2.warpPerspective(srcImg, M, dstSize)
    return dstImg

# xRange: [xmin, xmax], yRange: [ymin, ymax]　で srcImgを切り抜く
# keepAspectRatio=Trueで、srcImgの縦横比を保持する
# keepInsideImg=Trueで、画像内をはみ出して切り出すことが無いようにする
def cropRectImage(srcImg, xRange, yRange, dstSize, keepAspectRatio=False, keepInsideImg=False):
    height, width = srcImg.shape[:2]

    if keepAspectRatio:
        width = float(width)
        height = float(height)
        aRatio = height/width

        w = float(xRange[1] - xRange[0])
        h = float(yRange[1] - yRange[0])
        xMid = (xRange[0] + xRange[1]) * 0.5
        yMid = (yRange[0] + yRange[1]) * 0.5

        if h/w > aRatio: #縦が長い
            w = h  /aRatio
        else:
            h = w * aRatio

        xRange = [int(xMid - w*0.5), int(xMid + w*0.5)]
        yRange = [int(yMid - h*0.5), int(yMid + h*0.5)]

    if keepInsideImg:
        if xRange[0] < 0:
            diff = -xRange[0]
            xRange = [0, xRange[1] + diff]
        elif xRange[1] >= width:
            diff = xRange[1] - (width-1)
            xRange = [xRange[0] - diff, width-1]

        if yRange[0] < 0:
            diff = -yRange[0]
            yRange = [0, yRange[1] + diff]
        elif yRange[1] >= height:
            diff = yRange[1] - (height-1)
            xRange = [yRange[0] - diff, height-1]

    corners = [[xRange[0], yRange[0]],\
               [xRange[0], yRange[1]],\
               [xRange[1], yRange[1]],\
               [xRange[1], yRange[0]]]

    return cropImage(srcImg, corners, dstSize)


#角度でセンシングされたエリアを作成する。(音源方向/視線など)
# srcImg: 元画像
# srcPoint: センサーの位置(原点) (pixels)
# dstPoint: 終点の位置 (pixels)
# sensingAngle: センサーの範囲の角度で方向ベクトルからの角度。 0の場合は直線(degrees)
# color: 描画する色・値 (sensingAngle=0で直線のときのみ)

def drawSensingDirection(srcImg, srcPoint, dstPoint, sensingAngle=0, color=255, thickness=1):
    srcPoint = np.array(srcPoint)
    dstPoint = np.array(dstPoint)

    if sensingAngle == 0:
        srcPoint = srcPoint.astype(np.int)
        dstPoint = dstPoint.astype(np.int)
        cv2.line(srcImg, (srcPoint[0], srcPoint[1]), (dstPoint[0], dstPoint[1]), color, thickness)

    else:
        dstPointCenter = dstPoint - srcPoint
        dstPointCenter = dstPointCenter.T

        #left
        a = math.radians(sensingAngle)
        R = np.array([[math.cos(a), -math.sin(a)],\
                      [math.sin(a), math.cos(a)]])
        dstPointLeft = np.dot(R, dstPointCenter)
        dstPointLeft = dstPointLeft + srcPoint

        #right
        a = -a
        R = np.array([[math.cos(a), -math.sin(a)],\
                      [math.sin(a), math.cos(a)]])
        dstPointRight = np.dot(R, dstPointCenter)
        dstPointRight = dstPointRight + srcPoint

        dstPointCenter = dstPointCenter + srcPoint

        corners = [srcPoint.astype(np.int), \
                   dstPointLeft.T.astype(np.int), \
                   dstPointCenter.T.astype(np.int), \
                   dstPointRight.T.astype(np.int)]
        corners = np.array(corners, dtype=np.int)

        cv2.fillConvexPoly(srcImg, corners, color)

    return srcImg


def boxToVertex(box):
    center = box[0]
    size = box[1]
    agl = box[2]

    hSize = [size[0] * 0.5, size[1] * 0.5]
    vertexVec = [[- hSize[0], 0],\
                 [0, hSize[1]],\
                 [hSize[0], 0],\
                 [0, - hSize[1]]]
    vertexVec = np.array(vertexVec)

    centerVec = [[center[0], center[1]],\
                 [center[0], center[1]],\
                 [center[0], center[1]],\
                 [center[0], center[1]]]

    a = math.radians(agl)
    R = np.array([[math.cos(a), -math.sin(a)],\
                      [math.sin(a), math.cos(a)]])
    vertexVec = np.dot(R, vertexVec.T)
    vertexVec = vertexVec.T

    vertexVec = vertexVec + centerVec

    return vertexVec.tolist()

def scaleImage(srcImg, scale):
    size = srcImg.shape[:2]
    dstSize = (int(size[1] * scale), int(size[0] * scale))
    dstImg = cv2.resize(srcImg, dstSize)
    return dstImg