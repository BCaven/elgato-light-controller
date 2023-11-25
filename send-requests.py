#!/usr/bin/env python3
from lightStripController import LightStrip, Room
from time import sleep
def main():
    """

    """
    room = Room()
    room.setup()

    transition = [ # NOTE: these are the normal yellow/reds
        (34.0, 69.0, 100, 1000, 5000),
        #(26.0, 98.0, 100, 0, 1000),
        (1.0, 85.0, 100, 0, 5000),
        (1.0, 85.0, 0, 1000, 5000)

    ]
    room.room_transition(transition)

if __name__ == "__main__":
    main()
