#!/usr/bin/env python3
from lightStripController import LightStrip
from time import sleep
def main():
    """

    """
    lightstrips = LightStrip.find_light_strips_zeroconf()
    for light in lightstrips:
        data = light.get_strip_data()
        print(data)
    print("making the lights go in a rainbow then return to its original color")
    original_data = [light.get_strip_data() for light in lightstrips]
    for hue in range(0, 256):
        sleep(0.01)
        for light in lightstrips:
            light.update_color(1, hue, 100, 100)

    for i in range(len(lightstrips)):
        lightstrips[i].set_strip_data(original_data[i])


if __name__ == "__main__":
    main()
