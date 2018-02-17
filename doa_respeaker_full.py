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

MIC_DISTANCE_SIDE = 0.058
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
#                {
#                    "mic1": 0,
#                    "mic2": 1,
#                    "max_tdoa": MAX_TDOA_SIDE,
#                    "angle_offset": 0.0 # |
#                },
                {
                    "mic1": 0,
                    "mic2": 2,
                    "max_tdoa": MAX_TDOA_DIAG,
                    "angle_offset": 0.25*math.pi # \
                },
#                {
#                    "mic1": 0,
#                    "mic2": 3,
#                    "max_tdoa": MAX_TDOA_SIDE,
#                    "angle_offset": -math.pi/2 # -
#                },
#                {
#                    "mic1": 1,
#                    "mic2": 2,
#                    "max_tdoa": MAX_TDOA_SIDE,
#                    "angle_offset": -math.pi/2 # -
#                },
                {
                    "mic1": 1,
                    "mic2": 3,
                    "max_tdoa": MAX_TDOA_DIAG,
                    "angle_offset": 0.75*math.pi # /
                },
#                {
#                    "mic1": 2,
#                    "mic2": 3,
#                    "max_tdoa": MAX_TDOA_SIDE,
#                    "angle_offset": 0.0 # |
#                }
                ]

    def put(self, data):
        self.queue.append(data)

        super(DOA, self).put(data)

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
            cc, max_shift = gcc_phat(buf[m1idx::4], buf[m2idx::4], fs=self.sample_rate, max_tau=maxTDOA)
            for i in range(0, len(cc)):
              tau = (i - max_shift) / float(self.sample_rate)
              sineVal = tau / maxTDOA
              arcsine = np.arcsin(sineVal) 
              theta = math.fmod((np.arcsin(sineVal)-angleOffset+4.0*math.pi), 2.0*math.pi)
              print "i: "+str(i)+",sineVal: "+str(sineVal)+",arcsine: "+str(arcsine)+",theta: "+str(theta)
              self.angleHisto[(int)(theta/self.anglePerDiv)] += cc[i]
       
        print self.angleHisto
        best_guess = np.argmax(self.angleHisto)*self.anglePerDiv*(180.0/math.pi)
        sys.exit(0)
        return best_guess