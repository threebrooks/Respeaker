# -*- coding: utf-8 -*-

"""
Time Difference of Arrival for ReSpeaker 4 Mic Array
"""

import numpy as np
import collections
from gcc_phat import gcc_phat
from voice_engine.element import Element
import math


SOUND_SPEED = 340.0

MIC_DISTANCE_SIDE = 0.0572
MAX_TDOA_SIDE = MIC_DISTANCE_SIDE / float(SOUND_SPEED)
MAX_TDOA_DIAG = math.sqrt(2.0)*MAX_TDOA_SIDE

class DOA(Element):
    def __init__(self, rate=48000, chunks=10):
        super(DOA, self).__init__()

        self.queue = collections.deque(maxlen=chunks)
        self.sample_rate = rate

        self.angleDivs = 16
        self.anglePerDiv = 2*math.pi/self.angleDivs
        self.angleHisto = [0]*self.angleDivs

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
        self.queue.append(data)

        #print "len: "+str(len(data))

        #self.audioWriter.write(data)
        #self.audioWriter.flush()

        super(DOA, self).put(data)

    def rad2Deg(self, rad):
        return 180.0*rad/math.pi

    def deg2Rad(self, deg):
        return deg*math.pi/180.0

    def wrapAngle(self, angle):
        twoPi = 2.0*math.pi
        return angle-twoPi*math.floor(angle/twoPi)

    def get_direction(self):
        tau = [0, 0]
        theta = [0, 0]

        buf = b''.join(self.queue)
        buf = np.fromstring(buf, dtype='int16')

        self.angleHisto = [0]*len(self.angleHisto)

        for arrayIdx, dic in enumerate(self.pairs):
            m1idx = dic["mic1"]
            m2idx = dic["mic2"]
            maxTDOA = dic["max_tdoa"]
            angleOffset = dic["angle_offset"]
            cc, max_shift = gcc_phat(buf[m2idx::4], buf[m1idx::4], fs=self.sample_rate, max_tau=maxTDOA)
            for i in range(0, len(cc)):
              tau = (i - max_shift) / float(self.sample_rate)
              ratVal = tau / maxTDOA
              angle = math.pi/2-np.arcsin(ratVal)
              theta1 = self.wrapAngle(angle-angleOffset)
              theta1Idx = (int)(theta1/self.anglePerDiv) 
              self.angleHisto[theta1Idx] += cc[i]

              theta2 = self.wrapAngle((2*math.pi-angle)-angleOffset)
              theta2Idx = (int)(theta2/self.anglePerDiv) 
              self.angleHisto[theta2Idx] += cc[i]

        outList = []
        maxScore = np.max(self.angleHisto)
        for i in range(0, len(self.angleHisto)):
            outList.append([self.rad2Deg(i*self.anglePerDiv), self.angleHisto[i]/maxScore])
        return outList
