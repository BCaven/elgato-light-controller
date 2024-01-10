"""
controller for elgato light strips.

Reference: github.com/zunderscore/elgato-light-control/
"""

import requests
import socket
import json
from time import sleep, time
NUM_PORTS = 65536
ELGATO_PORT = 9123


class ServiceListener:
    """Listener for Zeroconf."""

    def __init__(self):
        """Init the listener."""
        self.services = []

    def get_services(self):
        """Return the services."""
        return self.services

    def remove_service(self, zeroconf, type, name):
        """Remove a service."""
        info = zeroconf.get_service_info(type, name)
        self.services.remove(info)

    def update_service(self, zeroconf, type, name):
        """Update a service."""
        # print("update was called")
        # info = zeroconf.get_service_info(type, name)
        # index = self.services.index(info)
        # self.services[index] =

    def add_service(self, zeroconf, type, name):
        """Add a service to the list."""
        info = zeroconf.get_service_info(type, name)
        self.services.append(info)


class Scene:
    """
    Store and manipulate scenes at a high level.

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
        """Init the scene."""
        for item in input_scene:
            assert type(item) is dict, f"TypeError: item: {item} is type: {type(item)} not type: dict"
        self.data = input_scene

    def add_scene(self, hue, saturation, brightness, durationMs, transitionMs):
        """Add an item to the end of the list."""
        self.data.append(
            {'hue': hue,
             'saturation': saturation,
             'brightness': brightness,
             'durationMs': durationMs,
             'transitionMs': transitionMs})

    def insert_scene(self,
                     index,
                     hue,
                     saturation,
                     brightness,
                     durationMs,
                     transitionMs):
        """Insert a scene in the list."""
        self.data.insert(
            index,
            {'hue': hue,
             'saturation': saturation,
             'brightness': brightness,
             'durationMs': durationMs,
             'transitionMs': transitionMs})

    def delete_scene(self, index=0):
        """Remove a scene from the list."""
        return self.data.pop(index)

    def print_scenes(self):
        """Display every scene in the loop."""
        for scene in self.data:
            print(scene)

    def length(self):
        """Return the duration of the scene."""
        scene_length = 0
        for scene in self.data['scene']:
            scene_length += scene['durationMs']
            scene_length += scene['transitionMs']
        return scene_length


def save_timer_to_file(file: str, time: str, lights: list, scene: list):
    """
    Save a timer in file so the controller can read it in.

        Format: TIME, LIGHT|LIGHT|etc, SCENE, SCENE, SCENE, etc
        TIME    = HHMM
        LIGHT   = ip addr : port
        SCENE   = HUE|SATURATION|BRIGHTNESS|DURATION_MS|TRANSITION_MS
    """
    with open(file, 'a') as output_file:
        output_list = [time, "|".join(lights)]
        for item in scene:
            output_list.append("|".join(str(s) for s in item))
        output_str = ",".join(output_list) + "\n"
        output_file.write(output_str)


class LightStrip:
    """
    LightStrip language.

    data: json object,  can be retrieved by making a get request to
    light.full_addr/elgato/lights
            always has two keys:
                'numberOfLights': int
                'lights'        : list
            each item in 'lights' is a dict that always has two keys:
                'on'            : int
                'brightness'    : int
            however, the lights have two (known) modes: individual colors, and scenes
                for individual colors, the dictionary additionally has 'hue' and
                'saturation' keys (both are of type `float`)
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
        """Initialize the light."""
        self.addr = addr
        self.port = port
        self.name = name
        self.full_addr = self.addr + ':' + str(self.port)
        self.get_strip_data()  # fill in the data/info/settings of the light
        self.get_strip_info()
        self.get_strip_settings()
        self.is_scene = False
        if 'scene' in self.data['lights'][0]:
            self.is_scene = True
            self.scene = Scene(self.data['lights'][0]['scene'])
        elif 'name' in self.data['lights'][0]:
            self.is_scene = True

    def find_light_strips_zeroconf(service_type='_elg._tcp.local.', TIMEOUT=15):
        """
        Use multicast to find all elgato light strips.

            Parameters:
                the service type to search
                the timeout period to wait until you stop searching
        """
        # NOTE: need to put this in a try/except statement
        # just in case they have not imported zeroconf
        try:
            import zeroconf
        except Exception:
            print("please install zeroconf to use this method")
            print("$ pip install zeroconf")
            return []

        lightstrips = []

        zc = zeroconf.Zeroconf()
        listener = ServiceListener()
        browser = zeroconf.ServiceBrowser(zc, service_type, listener)
        sleep(TIMEOUT)      # this is not a rolling admission... I could rework it to be that way, and it might be smarter to do that
        browser.cancel()    # however right now this works just fine. In theory it will lose connection to the lights if they get assigned to a new IP
                            # but in that case I am going to assume it is because the network bounces, which means this function will get called again anyways
        # print("Lights:")
        for service in listener.get_services():
            for addr in service.addresses:
                try:
                    prospect_light = LightStrip(socket.inet_ntoa(addr), service.port, service.get_name())
                    # TODO add support for Key Lights
                    if 'Strip' in prospect_light.info['productName']:
                        # print(f"\tadding light strip: {prospect_light.info['displayName']}")
                        lightstrips.append(prospect_light)
                except Exception:
                    pass
                    # print("Failed to connect to light")

        return lightstrips

    def start_rolling_admission_zeroconf(
            zeroconf, service_type='_elg._tcp.local.'):
        """Start a rolling admission for Zeroconf."""
        # TODO: write this method

    def find_light_strips_manual(strips) -> list:
        """TODO: write this method."""
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
        except Exception:
            pass

    def __check_all_ports(self, num_ports):
        for port in range(num_ports):
            yield LightStrip.__is_socket_open((self.addr, self.port))

    def get_strip_data(self):
        """
        Send a get request to the full addr.

            format:
            http://<IP>:<port>/elgato/lights
        """
        self.data = requests.get(
            'http://' + self.full_addr + '/elgato/lights',
            verify=False).json()
        return self.data

    def get_strip_info(self):
        """Send a get request to the light."""
        self.info = requests.get(
            'http://' + self.full_addr + '/elgato/accessory-info',
            verify=False).json()
        return self.info

    def get_strip_settings(self):
        """Get the strip's settings."""
        self.settings = requests.get(
            'http://' + self.full_addr + '/elgato/lights/settings',
            verify=False).json()
        return self.settings

    def get_strip_color(self):
        """
        Return the color of the light.

            If the light is not set to a specific color
            (i.e. when it is in a scene) then the tuple is empty
        """
        try:
            light_color = self.get_strip_data()['lights'][0]
            return (
                light_color['on'],
                light_color['hue'],
                light_color['saturation'],
                light_color['brightness'])
        except Exception:
            return ()  # the light strip is not set to a static color

    def set_strip_data(self, new_data: json) -> bool:
        """
        Send a put request to update the light data.

        Returns True if successful
        TODO: investigate if sending the entire JSON is necessary or if we can just send the things that need to be changed
        """
        # print("attempting message:")
        # print(json.dumps(new_data))
        try:
            r = requests.put(
                'http://' + self.full_addr + '/elgato/lights',
                data=json.dumps(new_data))
            # if the request was accepted, modify self.data
            if r.status_code == requests.codes.ok:
                self.data = r.json()
                return True
            # print("attempted message:")
            # print(json.dumps(new_data))
            # print("response:")
            print(r.text)
        except Exception:
            pass
        return False

    def set_strip_settings(self, new_data: json) -> bool:
        """
        Send a put request to update the light settings.

        Returns True on success
        """
        try:
            r = requests.put(
                'http://' + self.full_addr + '/elgato/lights/settings',
                data=json.dumps(new_data))
            print(r.text)
            if r.status_code == requests.codes.ok:
                self.settings = new_data
                return True
        except Exception:
            pass
        return False

    def set_strip_info(self, new_data: json) -> bool:
        """Set the strip info."""
        try:
            r = requests.put(
                'http://' + self.full_addr + '/elgato/accessory-info',
                data=json.dumps(new_data))
            if r.status_code == requests.codes.ok:
                self.info = new_data
                return True
            print(r.text)
        except Exception:
            pass
        return False

    def update_color(self, on, hue, saturation, brightness) -> bool:
        """User friendly way to interact with json data to change the color."""
        self.data = {
            'numberOfLights': 1,
            'lights': [
                {'on': on,
                 'hue': hue,
                 'saturation': saturation,
                 'brightness': brightness}
            ]
        }
        return self.set_strip_data(self.data)

    def update_scene_data(self, scene,
                          scene_name="transition-scene",
                          scene_id="",
                          brightness: float = 100.0):
        """Update just the scene data."""
        print("updating scene data")
        if not self.is_scene:
            print("light strip is not currently assigned to a scene, autogenerating")
            self.make_scene(scene_name, scene_id)

        if not scene:
            print("assigining scene by name")
            self.data['lights'][0]['name'] = scene_name
            if scene_id:
                print("also assigining scene by id")
                self.data['lights'][0]['id'] = scene_id
            print("purging scene data")
            if not self.data['lights'][0].pop('scene'):
                print("scene was not specified")
            if not self.data['lights'][0].pop('numberOfSceneElements'):
                print("number of scene elements was not specified")
        else:
            print("scene:", scene)
            assert type(scene) is Scene, "scene is not a list"
            self.data['lights'][0]['scene'] = scene.data
            self.data['lights'][0]['numberOfSceneElements'] = len(scene.data)

    def make_scene(self,
                   name: str,
                   scene_id: str,
                   brightness: float = 100.0):
        """Create a scene."""
        # print("making the light a scene")
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
        # if you do not specify an empty scene,
        # it might copy old scene data... annoying
        self.scene = Scene([])

    def transition_start(self,
                         colors: list,
                         name='transition-scene',
                         scene_id='transition-scene-id') -> tuple[int, bool]:
        """
        Non-blocking for running multiple scenes.

        returns how long to wait
        TODO: add ability to transition to a new scene

        TODO: see if scenes are callable by name
        TODO: make asyncronous function to replace this one

        TODO: see if you can pick a different way to cycle between colors in a scene
        """
        # print("---------transition starting")
        self.make_scene(name, scene_id, 100)
        wait_time_ms = 0
        # check if the light has already been set to a color,
        # and if it has, make that color the start of the transition scene
        if current_color := self.get_strip_color():
            _, hue, saturation, brightness = current_color
            self.scene.add_scene(
                hue,
                saturation,
                brightness,
                colors[0][3],
                colors[0][4])
            wait_time_ms += colors[0][4] + colors[0][3]
        # add the colors in the new scene
        for color in colors:
            hue, saturation, brightness, durationMs, transitionMs = color
            self.scene.add_scene(
                hue,
                saturation,
                brightness,
                durationMs,
                transitionMs)
            wait_time_ms += durationMs + transitionMs
        # update the light with the new scene
        self.update_scene_data(self.scene, scene_name=name, scene_id=scene_id)
        self.set_strip_data(self.data)
        # return the wait time
        return (wait_time_ms - colors[-1][3] - colors[-1][4]) / 1000

    def transition_end(self,
                       end_scene: list,
                       end_scene_name='end-scene',
                       end_scene_id='end-scene-id') -> bool:
        """
        End the transition scene and replace it with a new scene.

        used after transition_start is called
        sets the scene to the end_color
        almost identical to lightStrip.update_color - primarily used to keep code readable
        """
        # print("--------transition ending")
        assert type(end_scene) is list, f"TypeError: {end_scene} is type: {type(end_scene)} not type: list"
        # print("scene passed into transition_end:", end_scene)
        if not end_scene:  # TODO: make this cleaner
            # print("missing end scene, using scene name")
            self.update_scene_data(None, scene_name=end_scene_name, scene_id=end_scene_id)
            return self.set_strip_data(self.data)
        elif len(end_scene) == 1:
            # print("setting light to single color")
            hue, saturation, brightness, _, _ = end_scene[0]
            is_on = 1 if brightness > 0 else 0
            return self.update_color(is_on, hue, saturation, brightness)
        else:
            # the end scene is an actual scene
            # TODO: make scene brightness variable
            # print("setting transition to end on a scene")
            self.make_scene(end_scene_name, end_scene_id, 100)
            self.scene = Scene([])
            for item in end_scene:
                hue, saturation, brightness, durationMs, transitionMs = item
                self.scene.add_scene(
                    hue, saturation, brightness, durationMs, transitionMs)
            self.update_scene_data(
                self.scene, scene_name=end_scene_name, scene_id=end_scene_id)
            return self.set_strip_data(self.data)


class Room:
    """Collection of lights that are on the same network."""

    def __init__(self, lights: list = []):
        """Init the room."""
        assert type(lights) is list, f"TypeError: {lights} is type: {type(lights)} not type: list"
        self.lights = lights

    def setup(self, service_type='_elg._tcp.local.', timeout=15):
        """Find all the lights."""
        self.lights = LightStrip.find_light_strips_zeroconf(
            service_type, timeout)
        return True if self.lights else False

    def room_color(self, on, hue, saturation, brightness):
        """Set color for the whole room."""
        for light in self.lights:
            light.update_color(on, hue, saturation, brightness)

    def room_scene(self, scene):
        """Set all lights in the room to a specific scene."""
        # TODO: write this method

    def room_transition(self,
                        colors: list,
                        name='transition-scene',
                        scene_id='transition-scene-id',
                        end_scene: list = [],
                        end_scene_name="end-scene",
                        end_scene_id="end-scene-id"):
        """
        Non blocking transition for all room lights.

        TODO: return status of https request
        """
        rescan = False
        if not colors:
            # print("cannot transition an empty scene")
            return

        times = []
        for light in self.lights:
            times.append((
                light,
                light.transition_start(colors, name, scene_id),
                time()))

        while times:
            # TODO: check if this can be optimized to use less
            light, sleep_time, start_time = times.pop(0)
            # light, transition_start_output, start_time = times.pop(0)
            # print(transition_start_output)
            # sleep_time, success = transition_start_output
            if sleep_time + start_time < time():
                transition_status = light.transition_end(
                    end_scene, end_scene_name, end_scene_id)
                # print("transition status: ", transition_status)
                rescan = rescan or not transition_status
                # print(rescan)
            else:
                times.append((light, sleep_time, start_time))
        if rescan:
            # print("rescanning because a light failed")
            self.setup()
        return not rescan

    def light_transition(self,
                         addr: str,
                         colors: list,
                         name='transition-scene',
                         scene_id='transition-scene-id',
                         end_scene: list = [],
                         end_scene_name="end-scene",
                         end_scene_id="end-scene-id"):
        """Non blocking transition for specific light in the room."""
        rescan = False
        if not colors:
            # print("cannot transition an empty scene")
            return
        if not end_scene:
            end_scene = colors[-1]
        times = []
        for light in self.lights:
            if light.addr == addr:
                times.append((
                    light,
                    light.transition_start(colors, name, scene_id),
                    time()))

        while times:
            light, transition_start_output, start_time = times.pop(0)
            sleep_time, success = transition_start_output
            if sleep_time + start_time < time():
                rescan = rescan or light.transition_end(
                        end_scene, end_scene_name, end_scene_id)
            else:
                times.append((light, sleep_time, start_time))

        return
        if rescan:
            # print("rescanning because a light failed")
            self.setup()
