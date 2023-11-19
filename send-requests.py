#!/usr/bin/env python3
from lightStripController import LightStrip
from time import sleep
def main():
    """

    """
    lightstrips = LightStrip.find_light_strips_zeroconf()


    #print(lightstrips[1].get_strip_data())
    #return
    transition = [ # NOTE: these are the normal yellow/reds
        (34.0, 69.0, 100, 1000, 5000),
        #(26.0, 98.0, 100, 0, 1000),
        (1.0, 85.0, 100, 0, 5000),
        (1.0, 85.0, 0, 1000, 5000)

    ]
    for light in lightstrips:
        light.transition(transition)

    #sleep(5)
    for light in lightstrips:
        light.update_color(1, 34.0, 69.0, 100)
    return

    for light in lightstrips:
        if light.is_scene:
            print(light.data)
            light.scene.add_scene(100, 80, 100, 1000, 1000)
            light.update_scene_data(light.scene)
            print("new data:\n", light.data)
            #light.scene.print_scenes()
            light.set_strip_data(light.data)
        else:
            light.make_scene('test-scene', 'test-scene-id', 100.0)
            for i in range(4):
                light.scene.add_scene(100, i * 30, 100, 1000, 1000)
            light.update_scene_data(light.scene)
            print("new data\n", light.data, sep="")
            light.set_strip_data(light.data)



    return

    color_change_duration = 100
    lightstrips = LightStrip.find_light_strips_zeroconf()
    for light in lightstrips:
        data = light.get_strip_data()
        print(light.settings)
        #if not light.update_color_change_duration(color_change_duration):
        #    return
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
