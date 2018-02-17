"""
Record audio from 4 mic array, and then search the keyword "snowboy".
After finding the keyword, Direction Of Arrival (DOA) is estimated.

The hardware is respeaker 4 mic array:
    https://www.seeedstudio.com/ReSpeaker-4-Mic-Array-for-Raspberry-Pi-p-2941.html
"""


import time
from voice_engine.source import Source
from doa_respeaker_full import DOA
from pixels import pixels

def main():
    src = Source(rate=48000, channels=4, frames_size=320)
    doa = DOA(rate=48000)

    src.link(doa)

    src.recursive_start()
    while True:
        try:
            time.sleep(1)
            position = doa.get_direction()
            pixels.wakeup(position)
            print('detected at direction {}'.format(position))
        except KeyboardInterrupt:
            break

    src.recursive_stop()


if __name__ == '__main__':
    main()
