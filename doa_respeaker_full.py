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
                    "angle_offset": self.deg2Rad(-135)
                },
#                {
#                    "mic1": 1,
#                    "mic2": 3,
#                    "max_tdoa": MAX_TDOA_DIAG,
#                    "angle_offset": 0.5*math.pi
#                },
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

    def get_direction(self):
        tau = [0, 0]
        theta = [0, 0]

        buf = b''.join(self.queue)
        buf = np.fromstring(buf, dtype='int16')

        self.angleHisto = [1]*len(self.angleHisto)

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
works well with 0 offset, but jumps with anything else
              theta1 = math.fmod((angle-angleOffset+4.0*math.pi), 2.0*math.pi)
              theta1Idx = (int)(theta1/self.anglePerDiv) 
              self.angleHisto[theta1Idx] += cc[i]

              theta2 = math.fmod(((2*math.pi-angle)-angleOffset+4.0*math.pi), 2.0*math.pi)
              theta2Idx = (int)(theta2/self.anglePerDiv) 
              self.angleHisto[theta2Idx] += cc[i]
              #print "cv: {} theta1: {} cc: {} ".format(ratVal, self.rad2Deg(theta1), self.angleHisto[theta1Idx])
              #print "cv: {} theta2: {} cc: {} ".format(ratVal, self.rad2Deg(theta2), self.angleHisto[theta2Idx])
              #print "ratVal: {} arcsine: {} theta1: {} theta2: {} angleOffset {} ".format(sineVal, self.rad2Deg(arcsine), self.rad2Deg(theta1), self.rad2Deg(theta2), self.rad2Deg(angleOffset))

            #sys.exit(0)
       
        best_index = np.argmax(self.angleHisto) 
        for i in range(0, len(self.angleHisto)):
            print str(self.rad2Deg(i*self.anglePerDiv))+": "+str(self.angleHisto[i])+("  ######" if i == best_index else "")
        #print self.angleHisto
        best_guess = self.rad2Deg(best_index*self.anglePerDiv )
        #print "best_guess: "+str(best_guess)
        #sys.exit(0)
        return best_guess
