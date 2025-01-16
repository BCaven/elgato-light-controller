"""
controller for elgato light strips.

Reference: github.com/zunderscore/elgato-light-control/
"""

import requests
import socket
import json
from time import sleep, time
from concurrent.futures import ThreadPoolExecutor, as_completed

NUM_PORTS = 65536
ELGATO_PORT = 9123


import logging

from zeroconf import ServiceListener
# TODO: fix bug where listener crashes when a light is removed
class LightServiceListener(ServiceListener):
    """
    Listener for Zeroconf to keep track of active lights.
    Abusing passing by reference to keep track of active lights.
    """

    def __init__(self, light_dict: dict):
        """Initialize the listener."""
        self.log = logging.getLogger(__name__)
        self.log.info("Initializing LightServiceListener")
        self.light_dict = light_dict

    def remove_service(self, zeroconf, type, name):
        """
        Remove a service.
        
        Of course, the default timeout for this (when something is unplugged)
        is an hour
        TODO: change that timeout

        Right now, I am just deleting the light from the service dict in
        Room.check_for_new_lights()
        """
        if name in self.light_dict:
            try:
                del self.light_dict[name]
                self.log.critical(f"Removed light service: {name}")
            except Exception as e:
                self.log.error(f"Failed to remove light service: {e}")

    def update_service(self, zeroconf, type, name):
        """Update a service."""
        info = zeroconf.get_service_info(type, name)
        if info:
            self.light_dict[name] = info
            self.log.critical(f"Updated light service: {name}")

    def add_service(self, zeroconf, type, name):
        """Add a service to the list."""
        info = zeroconf.get_service_info(type, name)
        if info:
            self.light_dict[name] = info
            self.log.critical(f"Added light service: {name}")

    def get_active_lights(self):
        """Return the active lights."""
        self.log.info(f"Returning active lights: {self.light_dict}")
        return self.light_dict


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
        self.log = logging.getLogger(__name__)
        for item in input_scene:
            if not isinstance(item, dict):
                self.log.warning(f"TypeError: item: {item} is type: {type(item)} not type: dict")
                raise ValueError(f"Input scene item must be a dictionary, got {type(item)}")
        self.data = [] if not input_scene else input_scene.copy()

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
            self.log.info(scene)

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
        # Configure logging
        self.log = logging.getLogger(__name__)
        self.log.info(f"Initializing LightStrip with address: {addr}:{port}")
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

    def get_strip_data(self):
        """
        Send a get request to the full addr.

            format:
            http://<IP>:<port>/elgato/lights
        """
        self.data = requests.get(
            f'http://{self.full_addr}/elgato/lights',
            verify=False).json()
        return self.data

    def get_strip_info(self):
        """Send a get request to the light."""
        self.info = requests.get(
            f'http://{self.full_addr}/elgato/accessory-info',
            verify=False).json()
        return self.info

    def get_strip_settings(self):
        """Get the strip's settings."""
        self.settings = requests.get(
            f'http://{self.full_addr}/elgato/lights/settings',
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
        # self.log.debug("attempting message:")
        # self.log.debug(json.dumps(new_data))
        try:
            r = requests.put(
                'http://' + self.full_addr + '/elgato/lights',
                data=json.dumps(new_data))
            # if the request was accepted, modify self.data
            if r.status_code == requests.codes.ok:
                self.data = r.json()
                return True
            # self.log.debug("attempted message:")
            # self.log.debug(json.dumps(new_data))
            # self.log.debug("response:")
            self.log.debug(r.text)
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
            self.log.debug(r.text)
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
            self.log.debug(r.text)
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
        self.log.info("updating scene data")
        if not self.is_scene:
            self.log.info("light strip is not currently assigned to a scene, autogenerating")
            self.make_scene(scene_name, scene_id)

        if not scene:
            self.log.info("assigining scene by name")
            self.data['lights'][0]['name'] = scene_name
            if scene_id:
                self.log.info("also assigining scene by id")
                self.data['lights'][0]['id'] = scene_id
            self.log.info("purging scene data")
            if not self.data['lights'][0].pop('scene'):
                self.log.info("scene was not specified")
            if not self.data['lights'][0].pop('numberOfSceneElements'):
                self.log.info("number of scene elements was not specified")
        else:
            self.log.info(f"scene: {scene}")
            assert type(scene) is Scene, "scene is not a list"
            self.data['lights'][0]['scene'] = scene.data
            self.data['lights'][0]['numberOfSceneElements'] = len(scene.data)

    def make_scene(self,
                   name: str,
                   scene_id: str,
                   brightness: float = 100.0):
        """Create a scene."""
        # self.log.debug("making the light a scene")
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
                         scene_id='transition-scene-id') -> int:
        """
        Non-blocking for running multiple scenes.

        returns how long to wait
        TODO: add ability to transition to a new scene

        TODO: see if scenes are callable by name
        TODO: make asyncronous function to replace this one

        TODO: see if you can pick a different way to cycle between colors in a scene
        """
        # self.log.debug("---------transition starting")
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
        # self.log.debug("--------transition ending")
        assert type(end_scene) is list, f"TypeError: {end_scene} is type: {type(end_scene)} not type: list"
        # self.log.debug(f"scene passed into transition_end: {end_scene}")
        if not end_scene:  # TODO: make this cleaner
            # self.log.debug("missing end scene, using scene name")
            self.update_scene_data(None, scene_name=end_scene_name, scene_id=end_scene_id)
            return self.set_strip_data(self.data)
        elif len(end_scene) == 1:
            # self.log.debug("setting light to single color")
            hue, saturation, brightness, _, _ = end_scene[0]
            is_on = 1 if brightness > 0 else 0
            return self.update_color(is_on, hue, saturation, brightness)
        else:
            # the end scene is an actual scene
            # TODO: make scene brightness variable
            # self.log.debug("setting transition to end on a scene")
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

    def __init__(self, lights: list=[]):
        """Init the room."""
        if not lights:
            lights = []
        if not isinstance(lights, list):
            raise ValueError(f"TypeError: {lights} is type: {type(lights)} not type: list")
        self.lights: list[LightStrip] = lights
        self.service_dict = dict()
        self.log = logging.getLogger(__name__)
    
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
        except ImportError:
            raise ImportError("Please install zeroconf to use this method. You can install it using: pip install zeroconf")
    
        zc = zeroconf.Zeroconf()
        service_dict = dict()
        listener = LightServiceListener(service_dict)
        browser = zeroconf.ServiceBrowser(zc, service_type, listener)
        sleep(TIMEOUT)
        browser.cancel()
        new_lights = []
        for name, info in listener.get_active_lights().items():
            for addr in info.addresses:
                try:
                    prospect_light = LightStrip(socket.inet_ntoa(addr), info.port, name)
                    if 'Strip' in prospect_light.info['productName']:
                        new_lights.append(prospect_light)
                        logging.getLogger(__name__).info(f"Found new light strip: {prospect_light.info['displayName']}")
                except Exception as e:
                    logging.getLogger(__name__).error(f"Failed to connect to light: {e}")
        return new_lights
        

    def start_rolling_admission_zeroconf( 
            self, service_type='_elg._tcp.local.', timeout=15):
        """Start a rolling admission for Zeroconf."""
        try:
            import zeroconf
        except ImportError:
            raise ImportError("Please install zeroconf to use this method. You can install it using: pip install zeroconf")

        self.log.info("Starting rolling admission for Zeroconf")
        self.zeroconf = zeroconf.Zeroconf()
        self.service_type = service_type
        self.listener = LightServiceListener(self.service_dict)
        self.browser = zeroconf.ServiceBrowser(self.zeroconf, self.service_type, self.listener)
        sleep(timeout)

    def stop_rolling_admission_zeroconf(self):
        """Stop the rolling admission for Zeroconf."""
        if hasattr(self, 'browser'):
            self.browser.cancel()
            self.zeroconf.close()
            self.log.info("Stopped rolling admission for Zeroconf")
        else:
            self.log.warning("No active rolling admission to stop")

    def add_a_new_light(self, name: str, info):
        """Add a new light to the list."""
        new_lights = []
        for addr in info.addresses:
            try:
                prospect_light = LightStrip(socket.inet_ntoa(addr), info.port, name)
                if 'Strip' in prospect_light.info['productName']:
                    new_lights.append(prospect_light)
                    self.log.info(f"Found new light strip: {prospect_light.info['displayName']}")
            except Exception as e:
                self.log.debug(f"Failed to connect to light... skipping\n{e}")
        self.lights.extend(new_lights)

    def check_for_new_lights(self):
        """Check for new lights and add them to the list."""
        new_lights = []
        self.log.info("Checking for new lights")
        for name, info in self.service_dict.items():
            for addr in info.addresses:
                try:
                    prospect_light = LightStrip(socket.inet_ntoa(addr), info.port, name)
                    if 'Strip' in prospect_light.info['productName']:
                        new_lights.append(prospect_light)
                        self.log.info(f"Found new light strip: {prospect_light.info['displayName']}")
                except Exception as e:
                    self.log.debug(f"Failed to connect to light... skipping\n{e}")
        self.lights = new_lights
        return True

    def cleanup_inactive_services(self):
        """Remove inactive services from the list of lights."""
        active_lights = set(self.service_dict.keys())
        # if we have new lights, add them to self.lights
        if active_lights - set(light.name for light in self.lights):
            self.log.info("Found new lights, checking for them")
            for name in active_lights - set(light.name for light in self.lights):
                self.add_a_new_light(name, self.service_dict[name])
        inactive_lights = set(light.name for light in self.lights if light.name not in active_lights)
        if inactive_lights: 
            self.log.info("Cleaning up inactive services %s", inactive_lights)
            self.lights = [light for light in self.lights if light.name in active_lights]

    def setup(self, service_type='_elg._tcp.local.'):
        """Find all the lights."""
        self.log.info("Setting up room")
        self.start_rolling_admission_zeroconf(service_type=service_type)
        self.check_for_new_lights()
        return True if self.lights else False

    def room_color(self, on, hue, saturation, brightness):
        """Set color for the whole room."""
        for light in self.lights:
            light.update_color(on, hue, saturation, brightness)

    def room_scene(self, scene: Scene):
        """Set all lights in the room to a specific scene using a thread pool."""
        def update_light_scene(light: LightStrip):
            light.update_scene_data(scene.copy())
            return light.set_strip_data(light.data)
        
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(update_light_scene, light) for light in self.lights]
            
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        
        # Check if all updates were successful
        return all(results)
    
    def room_transition_threaded(self,
                                 colors: list,
                                 name='transition-scene',
                                 scene_id='transition-scene-id',
                                 end_scene: list = [],
                                 end_scene_name="end-scene",
                                 end_scene_id="end-scene-id") -> tuple[str]:
        """
        Non-blocking transition for all room lights using a thread pool.

        Returns tuple of successful names
        """
        if not colors:
            self.log.warning("Cannot transition an empty scene")
            return False

        def process_light_transition(light: LightStrip):
            assert type(light) is LightStrip, f"TypeError: {light} is type: {type(light)} not type: LightStrip"
            sleep_time = light.transition_start(colors.copy(), name, scene_id)
            self.log.info(f"Sleep time: {sleep_time}")
            sleep(sleep_time)
            transition_status = light.transition_end(end_scene, end_scene_name, end_scene_id)
            return transition_status

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_light_transition, light) for light in self.lights]
            
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        successful_lights = [light.name for light, result in zip(self.lights, results) if result]
        return tuple(successful_lights)

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
            self.log.warning("cannot transition an empty scene")
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
            self.log.debug(f"Processing light: {light}, sleep_time: {sleep_time}, start_time: {start_time}")
            
            if sleep_time + start_time < time():
                transition_status = light.transition_end(
                    end_scene, end_scene_name, end_scene_id)
                self.log.info(f"Transition status: {transition_status}")
                rescan = rescan or not transition_status
                self.log.debug(f"Rescan status: {rescan}")
            else:
                times.append((light, sleep_time, start_time))
        
        if rescan:
            self.log.warning("A light failed to transition, rescan recommended")
            #self.setup()
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
            self.log.warning("cannot transition an empty scene")
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

