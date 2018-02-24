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

MIC_DISTANCE_SIDE = 0.0572
MAX_TDOA_SIDE = MIC_DISTANCE_SIDE / float(SOUND_SPEED)
MAX_TDOA_DIAG = math.sqrt(2.0)*MAX_TDOA_SIDE

class DOA(Element):
    def __init__(self, rate=48000, chunks=10):
        super(DOA, self).__init__()

        self.audio_queue = collections.deque(maxlen=chunks)
        self.sample_rate = rate

        self.pairs = [
                {
                    "mic1": 0,
                    "mic2": 2,
                    "max_tdoa": MAX_TDOA_DIAG,
                    "angle_offset": self.deg2Rad(135)
                },
                {
                    "mic1": 1,
                    "mic2": 3,
                    "max_tdoa": MAX_TDOA_DIAG,
                    "angle_offset": self.deg2Rad(45)
                },
                {
                    "mic1": 0,
                    "mic2": 1,
                    "max_tdoa": MAX_TDOA_SIDE,
                    "angle_offset": self.deg2Rad(180)
                },
                {
                    "mic1": 1,
                    "mic2": 2,
                    "max_tdoa": MAX_TDOA_SIDE,
                    "angle_offset": self.deg2Rad(90)
                },
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

    def get_direction(self):
        buf = b''.join(self.audio_queue)
        buf = np.fromstring(buf, dtype='int16')

        angleHisto = [[ -2.0 for x in range(360)] for y in range(len(self.pairs))]

        for arrayIdx, dic in enumerate(self.pairs):
            m1idx = dic["mic1"]
            m2idx = dic["mic2"]
            maxTDOA = dic["max_tdoa"]
            angleOffset = dic["angle_offset"]
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
            for arrayIdx, dic in enumerate(self.pairs):
                if (angleHisto[arrayIdx][angle] != -2.0):
                    sumVal += angleHisto[arrayIdx][angle] 
            outList[angle] = sumVal

        maxScore = np.max(outList)
        for angle in range(0, len(outList)):
            outList[angle] /= maxScore

        return outList
