"""
controller for elgato light strips

Reference: github.com/zunderscore/elgato-light-control/
"""

import requests
import socket
from multiprocessing import Pool
import json
from time import sleep

NUM_PORTS = 65536
ELGATO_PORT = 9123

class ServiceListener:
    def __init__(self):
        self.services = []
    def get_services(self):
        return self.services
    def remove_service(self, zeroconf, type, name):
        print("Service %s removed" % (name,))
    def update_service(self, zeroconf, type, name):
        pass
    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        self.services.append(info)

class Scene:
    """
        class to store and manipulate scenes at a high level
            {
                'numberOfLights': 1,
                'lights': [
                    {'on': 1,
                     'id': 'com.corsair.cc.scene.sunrise',
                     'name': 'Sunrise',
                     'brightness': 100.0,
                     'numberOfSceneElements': 4,
                     'scene': []
                     }
                ]
            }

    """
    def __init__(self, input_scene=[]):
        """

        """
        self.data = input_scene

    def add_scene(self, hue, saturation, brightness, durationMs, transitionMs):
        """
            add an item to the end of the list
        """
        self.data.append({'hue': hue, 'saturation': saturation, 'brightness': brightness, 'durationMs': durationMs, 'transitionMs': transitionMs})
    def insert_scene(self, index, hue, saturation, brightness, durationMs, transitionMs):
        """

        """
        self.data.insert(index, {'hue': hue, 'saturation': saturation, 'brightness': brightness, 'durationMs': durationMs, 'transitionMs': transitionMs})

    def delete_scene(self, index=0):
        return self.data.pop(index)

    def print_scenes(self):
        """
            Display every scene in the loop
        """
        #print(self.data['scene'])
        for scene in self.data['scene']:
            print(scene)

    def length(self):
        scene_length = 0
        for scene in self.data['scene']:
            scene_length += scene['durationMs']
            scene_length += scene['transitionMs']
        return scene_length
        
class LightStrip:
    """
        LightStrip language
        data: json object,  can be retrieved by making a get request to light.full_addr/elgato/lights
            always has two keys:
                'numberOfLights': int
                'lights'        : list
            each item in 'lights' is a dict that always has two keys:
                'on'            : int
                'brightness'    : int
            however, the lights have two (known) modes: individual colors, and scenes
                for individual colors, the dictionary additionally has 'hue' and 'saturation' keys (both are of type `float`)
                for scenes:
                    'id'                        : str
                    'name'                      : str
                    'numberOfSceneElements'     : int
                    'scene'                     : list
                each 'scene' is a list of dictionaries containing the following keys:
                    'hue'                       : float
                    'saturation'                : float
                    'brightness'                : float
                    'durationMs'                : int
                    'transitionMs'              : int
            when there is a 'scene', the light loops through each item in the scene
    """
    def __init__(self, addr, port, name=""):
        self.addr = addr
        self.port = port
        self.name = name
        self.full_addr = self.addr + ':' + str(self.port)
        #print("full addr", self.full_addr)
        self.get_strip_data() # fill in the data/info/settings of the light
        self.get_strip_info()
        self.get_strip_settings()
        self.is_scene = False
        if 'scene' in self.data['lights'][0]:
            self.is_scene = True
            self.scene = Scene(self.data['lights'][0]['scene'])

    def find_light_strips_zeroconf(service_type='_elg._tcp.local.', TIMEOUT=5):
        """
            Use multicast to find all elgato light strips
            Parameters:
                the service type to search
                the timeout period to wait until you stop searching
        """
        # NOTE: need to put this in a try/except statement just in case they have not imported zeroconf
        try:
            import zeroconf
        except Exception:
            print("please install zeroconf to use this method")
            print("$ pip install zeroconf")
            return []

        lightstrips = []

        #print("attempting to find everything on", service_type)
        zc = zeroconf.Zeroconf()
        listener = ServiceListener()
        browser = zeroconf.ServiceBrowser(zc, service_type, listener)
        sleep(TIMEOUT)      # this is not a rolling admission... I could rework it to be that way, and it might be smarter to do that
        browser.cancel()    # however right now this works just fine. In theory it will lose connection to the lights if they get assigned to a new IP
                            # but in that case I am going to assume it is because the network bounces, which means this function will get called again anyways
        for service in listener.get_services():
            #print("name", service.get_name())
            #print("properties:", service.properties)
            #print("port", service.port)
            for addr in service.addresses:
                #print("address:", socket.inet_ntoa(addr))
                lightstrips.append(LightStrip(socket.inet_ntoa(addr), service.port, service.get_name()))

        return lightstrips


    def find_light_strips_manual(strips) -> list:
        # oof we have to do it the hardcore way or just give up...
        lightstrips = []
        for (addr, port) in strips:
            lightstrips.append(LightStrip(addr, port))
        return lightstrips

    def __is_socket_open(tup):
        addr, port = tup
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            r = sock.connect_ex((addr, port))
            if r == 0:
                print("port:", port, "was open")
                return port
            else:
                return 0
                #print("port:", i, "was closed")
        except Exception:
            pass

    def check_all_ports(self, num_ports):
        for port in range(num_ports):
            yield LightStrip.__is_socket_open((self.addr, self.port))

    def get_strip_data(self):
        """
            Send a get request to the full addr
            format:
            http://<IP>:<port>/elgato/lights
        """
        self.data = requests.get('http://' + self.full_addr + '/elgato/lights', verify=False).json()
        return self.data

    def get_strip_info(self):
        """
            Send a get request to the light
            should get back something in this format:
        """
        self.info = requests.get('http://' + self.full_addr + '/elgato/accessory-info', verify=False).json()
        return self.info

    def get_strip_settings(self):
        """

        """
        self.settings = requests.get('http://' + self.full_addr + '/elgato/lights/settings', verify=False).json()
        return self.settings
    def get_strip_color(self):
        """

        """
        light_color = self.get_strip_data()['lights'][0]
        return (light_color['on'], light_color['hue'], light_color['saturation'], light_color['brightness'])


    def set_strip_data(self, new_data: json) -> bool:
        """
            Sends a put request to update the light data
            Returns True if successful
        """
        r = requests.put('http://' + self.full_addr + '/elgato/lights', data=json.dumps(new_data))
        # if the request was accepted, modify self.data
        if r.status_code == requests.codes.ok:
            self.data = r.json()
            return True
        print(r.text)
        return False
    def set_strip_settings(self, new_data: json) -> bool:
        """
            Send a put request to update the light settings
            Returns True on success
        """
        r = requests.put('http://' + self.full_addr + '/elgato/lights/settings', data=json.dumps(new_data))
        print(r.text)
        if r.status_code == requests.codes.ok:
            self.settings = new_data
            return True
        return False
    def set_strip_info(self, new_data: json) -> bool:
        r = requests.put('http://' + self.full_addr + '/elgato/accessory-info', data=json.dumps(new_data))
        if r.status_code == requests.codes.ok:
            self.info = new_data
            return True
        print(r.text)
        return False

    def update_color(self, on, hue, saturation, brightness):
        """
            User friendly way to interact with json data to change the color
        """
        self.data['lights'][0]['on'] = on
        self.data['lights'][0]['hue'] = hue
        self.data['lights'][0]['saturation'] = saturation
        self.data['lights'][0]['brightness'] = brightness
        return self.set_strip_data(self.data)
    def update_color_change_duration(self, duration):
        print("old setting:", self.settings['colorChangeDurationMs'])
        self.settings['colorChangeDurationMs'] = duration
        return self.set_strip_info(self.settings)

    def update_scene_data(self, scene):
        self.data['lights'][0]['scene'] = scene.data
        self.data['lights'][0]['numberOfSceneElements'] = len(scene.data)

    def make_scene(self, name: str, scene_id: str, brightness: float):
        self.data = {
            'numberOfLights': 1,
            'lights': [
                {'on': 1,
                 'id': scene_id,
                 'name': name,
                 'brightness': brightness,
                 'numberOfSceneElements': 0,
                 'scene': []
                 }
            ]
        }
        self.is_scene = True
        self.scene = Scene()

    def transition(colors: list):
        """
            TODO: write this function

        needs to make a scene that transitions between these two colors
        once the scene has looped through once, change the color to be the desired end color
        """
        # add every color in colors to a temp scene
        # update the light with the new scene
        # wait until the scene has been completed
        # set the light to the end color

class Room:
    """
        Collection of lights that are on the same network

    """
    def __init__():
        self.lights = []

    def setup(service_type='_elg._tcp.local.', timeout=5):
        self.lights = LightStrip.find_light_strips_zeroconf(service_type, timeout)

    def room_color(self, on, hue, saturation, brightness):
        for light in self.lights:
            light.update_color(on, hue, saturation, brightness)

    def room_scene(self, scene):
        """
            Set all lights in the room to a specific scene

        """
