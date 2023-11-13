#!/usr/bin/env python3
from lightStripController import LightStrip
from time import sleep
def main():
    """

    """
    lightstrips = LightStrip.find_light_strips_zeroconf()


    print(lightstrips[0].get_strip_data())
    print(lightstrips[1].get_strip_data())



    return
    color_change_duration = 100
    lightstrips = LightStrip.find_light_strips_zeroconf()
    for light in lightstrips:
        data = light.get_strip_data()
        print(light.settings)
        if not light.update_color_change_duration(color_change_duration):
            return
    print("making the lights go in a rainbow then return to its original color")
    original_data = [light.get_strip_color() for light in lightstrips]
    for hue in range(0, 256, 10):
        sleep(color_change_duration / 1000)
        for light in lightstrips:
            light.update_color(1, hue, 100, 100)

    for i in range(len(lightstrips)):
        on, hue, sat, bri = original_data[i]
        lightstrips[i].update_color(on, hue, sat, bri)


if __name__ == "__main__":
    main()
