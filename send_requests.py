#!/usr/bin/env python3
"""
Miscelaneous setup and testing.

"""

from lightStripLib import Room


def main():
    """Msin driver for program."""
    room = Room()
    room.setup()

    for light in room.lights:
        print(f"light: {light.data}")


if __name__ == "__main__":
    main()
