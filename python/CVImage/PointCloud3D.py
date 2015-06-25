# -*- coding: utf-8 -*-

import os, sys
import cv2
import numpy as np
import math

CVTIMAGE_NO_CHECK = 0
CVTIMAGE_USE_MIN = 1
CVTIMAGE_USE_MAX = 2


class PointCloud3D:
	def __init__(self):
		self.setupKinectParams(version=1)

	#3次元変換
	def transform(self, src, T, R):
		n = src.shape[0]
		T_mat = np.zeros((n, 3))
		T_mat[:, 0] = T[0]
		T_mat[:, 1] = T[1]
		T_mat[:, 2] = T[2]

		dst = R.dot(src.T) + T_mat.T
		return dst.T

	#Kinect用の初期化
	def setupKinectParams(self, version=1):
		self.kinect_hfov = 1.0140363  # 58.1 (degrees)
		self.kinect_vfov = 0.813323431  # 46.6 (degrees)
		self.kinect_height = 240
		self.kinect_width = 320

		if version == 2:  # Kinect v2
			self.kinect_hfov = 1.23220245  # 70.6 (degrees)
			self.kinect_vfov = 1.04719755  # 60 (degrees)
			self.kinect_height = 424
			self.kinect_width = 512

		projectionScale = [math.tan((self.kinect_hfov * 0.5)) / (self.kinect_width * 0.5),\
						   math.tan((self.kinect_vfov * 0.5)) / (self.kinect_height * 0.5)]


		imgCenter = [float(self.kinect_width) * 0.5, float(self.kinect_height * 0.5)]

		xIdxImg = np.tile(np.arange(self.kinect_width), self.kinect_height).reshape((self.kinect_height, self.kinect_width))
		xIdxImg = xIdxImg.astype(np.float16)
		yIdxImg = np.tile(np.arange(self.kinect_height), self.kinect_width).reshape((self.kinect_width, self.kinect_height))
		yIdxImg = yIdxImg.T
		yIdxImg = yIdxImg.astype(np.float16)

		self.xIdxImg = ((xIdxImg - imgCenter[0]) * projectionScale[0])
		self.yIdxImg = ((yIdxImg - imgCenter[1]) * projectionScale[1])

	#np.savetxt("testdata.txt", yIdxImg, delimiter=", ")

	# Kinectから読み込んでpoint cloudに変換する
	# ret: point_cloud: [[x,y,z] ....]
	def loadKinectImage(self, kinectImg):

		xIdxImg = self.xIdxImg * kinectImg
		yIdxImg = self.yIdxImg * kinectImg

		size = self.kinect_width*self.kinect_height
		points = np.vstack((xIdxImg.reshape(size), yIdxImg.reshape(size), kinectImg.reshape(size).astype(np.float16)))
		points = points.T

		points = np.delete(points, np.where(points[:, 2] == 0)[0], 0)

		#print points.shape

		return points

	#point cloudを画像に変換する
	def convertToImageDetail(self, points, xmin, xmax, ymin, ymax, zmin, zmax, width, height, type=CVTIMAGE_NO_CHECK):
		dtype = np.uint16

		if np.alen(points) == 0:
			dstImg = np.zeros((height, width), dtype=dtype)
			return dstImg

		xScale = float(width) / (xmax-xmin)
		yScale = float(height) / (ymax-ymin)

		points = points - np.array([xmin, ymin, 0])
		points = points * np.array([xScale, yScale, 1])

		points = points.astype(np.int16)

		points = np.delete(points, np.where(points[:, 0] < 0)[0], 0)
		points = np.delete(points, np.where(points[:, 0] >= width)[0], 0)
		points = np.delete(points, np.where(points[:, 1] < 0)[0], 0)
		points = np.delete(points, np.where(points[:, 1] >= height)[0], 0)
		points = np.delete(points, np.where(points[:, 2] < zmin)[0], 0)
		points = np.delete(points, np.where(points[:, 2] >= zmax)[0], 0)

		#print points

		a = [[1, width, 0],\
			 [0, 0, 1]]
		a = np.array(a)
		a = a.T

		points1D = points.dot(a)

		dstImgList = [0] * (width*height)

		pointsList = points1D.tolist()

		count = 0

		for p in pointsList:
			imgIdx = p[0]
			z = p[1]

			count = count + 1

			if type == CVTIMAGE_NO_CHECK:
				dstImgList[imgIdx] = z
			elif type == CVTIMAGE_USE_MIN:
				v = dstImgList[imgIdx]
				if v == 0 or v > z:
					dstImgList[imgIdx] = z
			elif type == CVTIMAGE_USE_MAX:
				v = dstImgList[imgIdx]
				if v == 0 or v < z:
					dstImgList[imgIdx] = z


		dstImg = np.array(dstImgList).reshape((height, width)).astype(dtype)

		return dstImg


	#point cloudを画像に変換する
	def convertToImage(self, points, xRange, yRange, zRange, pixel2mm, type=CVTIMAGE_NO_CHECK):
		w = xRange[1] - xRange[0]
		h = yRange[1] - yRange[0]

		w = int(w/pixel2mm)
		h = int(h/pixel2mm)

		return self.convertToImageDetail(points, xRange[0], xRange[1], yRange[0], yRange[1], zRange[0], zRange[1], w, h, type)