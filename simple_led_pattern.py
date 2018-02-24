
import numpy as np
import time
import math


class SimpleLedPattern(object):
    def __init__(self, show=None, number=12):
        self.pixels_number = number
        self.pixels = [0] * 4 * number

        if not show or not callable(show):
            def dummy(data):
                pass
            show = dummy

        self.show = show
        self.stop = False

    def showAngleScores(self, angleScores):
        pixels = [0, 0, 0, 0] * self.pixels_number
        maxAngle = np.argmax(angleScores)
        for angle in range(0,len(angleScores)):
            position = int((angle + 15) / (360 / self.pixels_number)) % self.pixels_number
            bright = int(50*math.pow(angleScores[angle], 4.0))
            if (bright > pixels[position * 4 + 2]): 
                rgbIdx = 1 if angle == maxAngle else 2
                pixels[position * 4 + rgbIdx] = bright

        self.show(pixels)

    def off(self):
        self.show([0] * 4 * 12)
