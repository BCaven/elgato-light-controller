#!/usr/bin/env python3
"""Miscelaneous setup and testing."""

from lightStripLib import Room


def main():
    """Msin driver for program."""
    room = Room()
    room.setup()

    for light in room.lights:
        print("light:")
        print(light.data)

    transition = [ # NOTE: these are the normal yellow/reds
        #(34.0, 69.0, 100, 1000, 5000),
        #(26.0, 98.0, 100, 0, 1000),
        #(1.0, 85.0, 100, 10, 5000),
        #(1.0, 85.0, 0, 100, 5000),
        #(34.0, 69.0, 100, 1000, 5000)
        #(30.0, 53.0, 100, 1000, 5000) # morning yellow
        (22.0, 56.0, 77, 1000, 5000), # evening yellow
        (276.0, 93.0, 63, 1000, 5000), # purple (thanos)

        # moody
        # (233.5, 100, 50.9, 1000, 5000),
        # (257.2, 86.9, 32.9, 1000, 5000),

        # smolder
        # (352.5, 100.0, 18.8, 1000, 1000),
        # (352.4, 100.0, 34.1, 1000, 1000),
        # (352.2, 100.0, 54.9, 1000, 1000),
        # (351.7, 100.0, 40.0, 1000, 1000),
        (352.0, 100.0, 58.8, 1000, 1000),
        (352.3, 100.0, 45.8, 1000, 1000)

    ]
    end_scene = [
        (233.5, 100, 50.9, 1000, 5000),
        (257.2, 86.9, 32.9, 1000, 5000)
    ]
    print("\nTransition starting...")
    room.room_transition(
        transition,
        name="transition-scene",
        scene_id="transition-scene-id",
        end_scene_name="Moody",
        end_scene_id="69a0d769-0a63-46c6-906b-3d9c2286455c",
        end_scene=end_scene)

    print("\nTransition ending...")

if __name__ == "__main__":
    main()
