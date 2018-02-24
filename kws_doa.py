import time
from voice_engine.source import Source
from doa_respeaker_full import DOA
from pixels import pixels
import numpy as np

def main():
    src = Source(rate=48000, channels=4, frames_size=4800)
    doa = DOA(rate=48000)

    src.link(doa)

    src.recursive_start()
    while True:
        try:
            time.sleep(0.2)
            angleScores = doa.get_direction()
            maxAngle = np.argmax(angleScores)
            pixels.showAngle(maxAngle)
            shifts = doa.get_shifts(maxAngle)
            print str(shifts)
        except KeyboardInterrupt:
            break

    src.recursive_stop()


if __name__ == '__main__':
    main()
