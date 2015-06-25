__author__ = 'LCDemo'

import cv2.cv as cv
import math


class Kalman2D:
    def __init__(self, measurement_noise_cov=1e-2):
        self.kalman = None
        self.init(measurement_noise_cov)

    def init(self, measurement_noise_cov=1e-2):
        self.kalman = None

        self.measurement_noise_cov = measurement_noise_cov

        self.kalman = cv.CreateKalman(4, 2)

        self.kalman.transition_matrix[0,0] = 1
        self.kalman.transition_matrix[0,1] = 0
        self.kalman.transition_matrix[0,2] = 1
        self.kalman.transition_matrix[0,3] = 0

        self.kalman.transition_matrix[1,0] = 0
        self.kalman.transition_matrix[1,1] = 1
        self.kalman.transition_matrix[1,2] = 0
        self.kalman.transition_matrix[1,3] = 1

        self.kalman.transition_matrix[2,0] = 0
        self.kalman.transition_matrix[2,1] = 0
        self.kalman.transition_matrix[2,2] = 1
        self.kalman.transition_matrix[2,3] = 0

        self.kalman.transition_matrix[3,0] = 0
        self.kalman.transition_matrix[3,1] = 0
        self.kalman.transition_matrix[3,2] = 0
        self.kalman.transition_matrix[3,3] = 1

        cv.SetIdentity(self.kalman.measurement_matrix, cv.RealScalar(1))
        cv.SetIdentity(self.kalman.process_noise_cov, cv.RealScalar(1e-5))
        cv.SetIdentity(self.kalman.measurement_noise_cov, cv.RealScalar(self.measurement_noise_cov))
        cv.SetIdentity(self.kalman.error_cov_post, cv.RealScalar(1))

        self.firstFlag = True
        self.firstPos = [0., 0.]


    def correct(self, pos):
        if self.firstFlag:
            self.firstPos = pos
            self.firstFlag = False

        measurement = cv.CreateMat(2, 1, cv.CV_32FC1)

        cv.Set1D(measurement,0, cv.Scalar(pos[0]-self.firstPos[0]))
        cv.Set1D(measurement,1, cv.Scalar(pos[1]-self.firstPos[1]))
        cv.KalmanCorrect(self.kalman, measurement)

    def predict(self):
        predict = cv.KalmanPredict(self.kalman)

        pos = [cv.Get1D(predict,0)[0]+self.firstPos[0], \
               cv.Get1D(predict,1)[0]+self.firstPos[1]]
        return pos

