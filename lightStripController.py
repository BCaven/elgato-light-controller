# Reference: github.com/zunderscore/elgato-light-control/

# Theory: lights are updated using http requests that are made to the light
# http://{ip addr}:{port}/elgato/
# stuff about the lights is found under /elgato/lights (this includes /lights/settings)
# general info is under /elgato/accessory-info

# TODO: check all light settings and reverse engineer http requests to update lights

# TODO: consider refactoring how lights are seen and delt with
# IDEA: perhaps just describe them as ip addresses/ports and only use the lightOptions stuff
#   Pro: saves space and headache
#   Con: technically ignores a lot of data, however, I do not know if this data is useful for internal project
#   Compromise: add increased functionality as a future TODO item


class LightOptions:
    def __init__(self, on: int, saturation: int, hue: int, brightness: int):
        self.on = on
        self.saturation = saturation
        self.hue = hue
        self.brightness = brightness

class Light:
    def __init__(self, ip: str, port: int, name:str):
        self.ip = ip
        self.port = port
        self.name = name
        self.powerOnBehavior = 0
        self.powerOnBrightness = 0
        self.powerOnTemperature = 0
        self.switchOnDurationMs = 0
        self.switchOffDurationMs = 0
        self.colorChangeDurationMs = 0
        self.productName = ""
        self.hardwareBoardType = 0
        self.firmwareBuildNumber = 0
        self.firmwareVersion = ""
        self.serialNumber = ""
        self.displayName = ""
        self.features = []
        self.numberOfLights = 0
        self.options = []

    def update_settings(self, options: LightOptions) -> None:
        self.options = options
        


def find_lights() -> list(Light):
    # when booting need to find all existing lights
    # I think this means go through all of the ip addrs on the network and see which one is a light
    # use nmap, same as method to find controller

    # However, this might be unnecessary here
    # should return a list of lights
    pass

def update_light(light: Light, options: LightOptions) -> int:
    # update one light
    # this method wil only be used by the controller, 
    pass

def update_lights(lights: list(Light)) -> int:
    for light in lights:
        update_light(light)
    pass
