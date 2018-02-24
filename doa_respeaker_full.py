# -*- coding: utf-8 -*-

"""
Time Difference of Arrival for ReSpeaker 4 Mic Array
"""

import numpy as np
import collections
from gcc_phat import gcc_phat
from voice_engine.element import Element
import math
import sys

SOUND_SPEED = 340.0
MIC_DIST_SIDE = 0.0572

class DOA(Element):
    def __init__(self, rate=48000, chunks=10):
        super(DOA, self).__init__()

        self.audio_queue = collections.deque(maxlen=chunks)
        self.sample_rate = rate

        self.mic_coords = [
                [-MIC_DIST_SIDE/2, -MIC_DIST_SIDE/2], # 0
                [-MIC_DIST_SIDE/2, MIC_DIST_SIDE/2], # 1
                [MIC_DIST_SIDE/2, MIC_DIST_SIDE/2], # 2
                [MIC_DIST_SIDE/2, -MIC_DIST_SIDE/2], # 3
                ]

        self.mic_pairs = [
                [0,2], [1,3], [0,1], [1,2]
                ]

    def put(self, data):
        self.audio_queue.append(data)

        super(DOA, self).put(data)

    def rad2Deg(self, rad):
        return 180.0*rad/math.pi

    def deg2Rad(self, deg):
        return deg*math.pi/180.0

    def wrapRadAngle(self, angle):
        twoPi = 2.0*math.pi
        return angle-twoPi*math.floor(angle/twoPi)

    def wrapDegAngle(self, angle):
        return angle-360*int(math.floor(angle/360))

    def cappedArcSin(self, val):
        if (val < -1.0):
            return -math.pi/2
        elif (val > 1.0):
            return math.pi/2
        else:
            return np.arcsin(val)

    def shift2Angle(self, shift, maxTDOA):
        tau = shift / float(self.sample_rate)
        angle = math.pi/2-self.cappedArcSin(tau / maxTDOA)
        return angle

    def getMicDistance(self, mic1, mic2):
        xDiff = mic1[0]-mic2[0]
        yDiff = mic1[1]-mic2[1]
        return math.sqrt(xDiff*xDiff+yDiff*yDiff)

    def getMicAngle(self, mic1, mic2):
        xDiff = mic2[0]-mic1[0]
        yDiff = mic2[1]-mic1[1]
        return math.pi/2+math.atan2(yDiff, xDiff)

    def get_direction(self):
        buf = b''.join(self.audio_queue)
        buf = np.fromstring(buf, dtype='int16')

        angleHisto = [[ -2.0 for x in range(360)] for y in range(len(self.mic_pairs))]

        for arrayIdx, mic_list in enumerate(self.mic_pairs):
            m1idx = mic_list[0]
            m2idx = mic_list[1]
            maxTDOA = self.getMicDistance(self.mic_coords[m1idx], self.mic_coords[m2idx])/SOUND_SPEED
            angleOffset = self.getMicAngle(self.mic_coords[m1idx], self.mic_coords[m2idx])
            cc, max_shift = gcc_phat(buf[m2idx::4], buf[m1idx::4], fs=self.sample_rate, max_tau=maxTDOA)
            
            for shift in range(0, len(cc)):
              startAngle = int(round(self.rad2Deg(self.shift2Angle(shift-max_shift+0.5, maxTDOA)-angleOffset)))
              endAngle = int(round(self.rad2Deg(self.shift2Angle(shift-max_shift-0.5, maxTDOA)-angleOffset)))

              for angle in range(startAngle, endAngle+1):
                  wrapAngle = self.wrapDegAngle(angle)
                  if (cc[shift] > angleHisto[arrayIdx][wrapAngle]):
                      angleHisto[arrayIdx][wrapAngle] = cc[shift]

              startAngle = int(round(self.rad2Deg((2*math.pi-self.shift2Angle(shift-max_shift-0.5, maxTDOA))-angleOffset)))
              endAngle = int(round(self.rad2Deg((2*math.pi-self.shift2Angle(shift-max_shift+0.5, maxTDOA))-angleOffset)))

              for angle in range(startAngle, endAngle+1):
                  wrapAngle = self.wrapDegAngle(angle)
                  if (cc[shift] > angleHisto[arrayIdx][wrapAngle]):
                      angleHisto[arrayIdx][wrapAngle] = cc[shift]

        outList = [0] * 360
        for angle in range(0, 360):
            sumVal = 0
            for arrayIdx, dic in enumerate(self.mic_pairs):
                if (angleHisto[arrayIdx][angle] != -2.0):
                    sumVal += angleHisto[arrayIdx][angle] 
            outList[angle] = sumVal

        maxScore = np.max(outList)
        for angle in range(0, len(outList)):
            outList[angle] /= maxScore

        return outList
