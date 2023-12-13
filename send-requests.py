#!/usr/bin/env python3
from lightStripLib import LightStrip, Room, save_timer_to_file
from time import sleep
def main():
    """

    """
    room = Room()
    room.setup()

    transition = [ # NOTE: these are the normal yellow/reds
        #(34.0, 69.0, 100, 1000, 5000),
        #(26.0, 98.0, 100, 0, 1000),
        (1.0, 85.0, 100, 10, 5000),
        (1.0, 85.0, 0, 100, 5000),
        (34.0, 69.0, 100, 1000, 5000)

    ]
    #save_timer_to_file("demo.transition", "2030", ["192.168.86.23:5123"], transition)
    room.room_transition(transition)

if __name__ == "__main__":
    main()
