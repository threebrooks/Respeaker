
import numpy
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
        for i in range(0,len(angleScores)):
            position = int((angleScores[i][0] + 15) / (360 / self.pixels_number)) % self.pixels_number
            bright = 50*math.pow(angleScores[i][1], 4.0)
            pixels[position * 4 + 2] = bright

        self.show(pixels)

    def off(self):
        self.show([0] * 4 * 12)
