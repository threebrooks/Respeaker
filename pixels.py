
import apa102
import time
import threading
import numpy as np
from gpiozero import LED
try:
    import queue as Queue
except ImportError:
    import Queue as Queue

class Pixels:
    PIXELS_N = 12

    def __init__(self):
        self.dev = apa102.APA102(num_led=self.PIXELS_N)
        
        self.power = LED(5)
        self.power.on()

        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()

    def showAngle(self, angle):
        pixels = [0, 0, 0, 0] * self.PIXELS_N
        position = int((angle + 15) / (360 / self.PIXELS_N)) % self.PIXELS_N
        pixels[position * 4 + 1] = 50
        self.show(pixels)

    def off(self):
        pixels = [0, 0, 0, 0] * self.PIXELS_N
        self.show(pixels)

    def _run(self):
        while True:
            func = self.queue.get()
            self.pattern.stop = False
            func()

    def show(self, data):
        for i in range(self.PIXELS_N):
            self.dev.set_pixel(i, int(data[4*i + 1]), int(data[4*i + 2]), int(data[4*i + 3]))

        self.dev.show()


pixels = Pixels()


if __name__ == '__main__':
    while True:

        try:
            pixels.off()
            time.sleep(3)
        except KeyboardInterrupt:
            break


    pixels.off()
    time.sleep(1)
