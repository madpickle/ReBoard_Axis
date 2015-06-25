# -*- coding: utf-8 -*-
import os, sys
import cv2
import numpy as np

#トラッキングした結果の矩形に関する処理

class TrackedArea:
    def __init__(self, width, height):
        self.width = width #image width
        self.height = height #image height

    #点がlineの線分中にあるか
    def isInside(self, point, line):
        xmin = min(line[0][0], line[1][0])
        xmax = max(line[0][0], line[1][0])
        ymin = min(line[0][1], line[1][1])
        ymax = max(line[0][1], line[1][1])

        if point[0] < xmin:
            return False
        if point[0] > xmax:
            return False
        if point[1] < ymin:
            return False
        if point[1] > ymax:
            return False

        return True

    def uniquePoints(self, points):
        dstPoints = []

        for point in points:
            flag = False
            for dstPoint in dstPoints:
                if point[0] == dstPoint[0] and point[1]==dstPoint[1]:
                    flag = True

            if flag == False:
                dstPoints.append(point)

        return dstPoints

    #交点を取得する
    #line: [[sx, sy], [ex, ey]]
    #rectangleLine: [[sx, sy], [ex, ey]]
    def getIntersectionPoint(self, line, rectangleLine):

        lineX1 = line[0][0]
        lineY1 = line[0][1]
        lineX2 = line[1][0]
        lineY2 = line[1][1]
        rectangleLineX1 = rectangleLine[0][0]
        rectangleLineY1 = rectangleLine[0][1]
        rectangleLineX2 = rectangleLine[1][0]
        rectangleLineY2 = rectangleLine[1][1]

        p = None
        d = (lineX1 - lineX2) * (rectangleLineY1 - rectangleLineY2)\
            - (lineY1 - lineY2) * (rectangleLineX1 - rectangleLineX2);
        if (d != 0) :
            xi = ((rectangleLineX1 - rectangleLineX2)\
                * (lineX1 * lineY2 - lineY1 * lineX2) - (lineX1 - lineX2)\
				* (rectangleLineX1 * rectangleLineY2 - rectangleLineY1 * rectangleLineX2)) / d
            yi = ((rectangleLineY1 - rectangleLineY2)\
				* (lineX1 * lineY2 - lineY1 * lineX2) - (lineY1 - lineY2)\
				* (rectangleLineX1 * rectangleLineY2 - rectangleLineY1 * rectangleLineX2)) / d
            p = [xi, yi]
        return p

    #画像の中心と矩形の中心を結ぶ線と矩形が交わる点を取得する
    #centerPoint: [x, y]
    #rectangle: [[x0, y0], [x1, y1], [x2, y2], [x3, y3]]
    def getIntersectionPoints(self, centerPoint, rectangle):
        line = [[self.width*0.5, self.height*0.5], centerPoint]
        intersectionPoints = []

        rectline = [rectangle[0], rectangle[1]]
        p = self.getIntersectionPoint(line, rectline)
        if p and self.isInside(p, rectline):
            intersectionPoints.append(p)

        rectline = [rectangle[1], rectangle[2]]
        p = self.getIntersectionPoint(line, rectline)
        if p and self.isInside(p, rectline):
            intersectionPoints.append(p)

        rectline = [rectangle[2], rectangle[3]]
        p = self.getIntersectionPoint(line, rectline)
        if p and self.isInside(p, rectline):
            intersectionPoints.append(p)

        rectline = [rectangle[3], rectangle[0]]
        p = self.getIntersectionPoint(line, rectline)
        if p and self.isInside(p, rectline):
            intersectionPoints.append(p)

        intersectionPoints = self.uniquePoints(intersectionPoints)

        if len(intersectionPoints) != 2:
            print "intersectionPoints is not 2"
            print intersectionPoints
            return None

        imageCenter = np.array([self.width*0.5, self.height*0.5])
        p0 = np.array(intersectionPoints[0])
        p1 = np.array(intersectionPoints[1])

        d0 = np.linalg.norm(p0)
        d1 = np.linalg.norm(p1)

        if d1 < d0:
            #flip points
            intersectionPoints = [intersectionPoints[1], intersectionPoints[0]]

        return intersectionPoints

