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

class LightStrip:
    """

    """
    def __init__(self, addr, port, name=""):
        self.addr = addr
        self.port = port
        self.name = name
        self.full_addr = self.addr + ':' + str(self.port)
        pass

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
            return

        lightstrips = []

        print("attempting to find everything on", service_type)
        zc = zeroconf.Zeroconf()
        listener = ServiceListener()
        browser = zeroconf.ServiceBrowser(zc, service_type, listener)
        sleep(TIMEOUT) # this is not a rolling admission... I could rework it to be that way, and it might be smarter to do that
        browser.cancel()
        for service in listener.get_services():
            print("name", service.get_name())
            print("properties:", service.properties)
            print("port", service.port)
            for addr in service.addresses:
                print("address:", socket.inet_ntoa(addr))
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
