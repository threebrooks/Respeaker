# -*- coding: utf-8 -*-

"""
Delay and sum
"""

import numpy as np
import collections
from gcc_phat import gcc_phat
from voice_engine.element import Element
import math
import sys
import operator 

class DelayAndSum(Element):
    def __init__(self, channels, chunks=10):
        super(DelayAndSum, self).__init__()

        self.num_channels = channels
        self.shifts = [0] * self.num_channels
        self.zero_shift_idx = -1
        self.last_cutoff = [0] * self.num_channels
        self.accumAudio = [[] for i in range(self.num_channels)]
        self.audioDump = open("audio.raw","wb")

    def put(self, data):
        super(DelayAndSum, self).put(data)
        
        newAudioRawBuf = np.fromstring(data, dtype='int16')
        for channel in range(self.num_channels):
            channelData = newAudioRawBuf[channel::self.num_channels] 
            self.accumAudio[channel].extend(channelData)

        zi_new_data_length = len(self.accumAudio[self.zero_shift_idx])-self.last_cutoff[self.zero_shift_idx]
        print "zi_new_data_length: "+str(zi_new_data_length)
        outAudioData = [0] * zi_new_data_length
        for channel in range(self.num_channels):
            startIdx = self.last_cutoff[channel]-self.shifts[channel] 
            endIdx = self.last_cutoff[channel]+zi_new_data_length-self.shifts[channel] 
            print str(startIdx)+"->"+str(endIdx)
            outAudioData = map(operator.add, outAudioData, self.accumAudio[channel][startIdx:endIdx])
            self.last_cutoff[channel] += zi_new_data_length
        byteArray = np.array(outAudioData, 'int16')
        byteArray.tofile(self.audioDump)
        self.audioDump.flush()


    def set_shifts(self, shifts):
        self.shifts = shifts
        for channel in range(self.num_channels):
            if (shifts[channel] == 0):
                self.zero_shift_idx = channel

