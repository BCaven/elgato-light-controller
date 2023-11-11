#!/usr/bin/env python3

import requests
import socket
from multiprocessing import Pool

# find the open port
ADDR = '192.168.86.25'
NUM_PORTS = 65536
PORT = 9123 # found using brute force... whoops
def is_socket_open(tup):
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

def check_all_ports(addr, num_ports):
   for i in range(num_ports):
       yield is_socket_open((addr, i))

def main():
    #port = check_all_ports(ADDR, NUM_PORTS)
    #for port in check_all_ports(ADDR, NUM_PORTS):
    #    if port == 0:
    #        continue
    #    print("port:", port, "was open")
    #
    # /elgato/lights/settings
    # /elgato/accessory-info
    # /elgato/lights <- make a put request here to change the light settings
    #
    # {"numberOfLights":1,"lights":[{"on":1,"hue":26.0,"saturation":98.0,"brightness":100}]}
    full_addr = 'http://' + ADDR + ':' + str(PORT) + '/elgato/lights'
    r = requests.get(full_addr, verify=False)
    json_data = r.json()
    print(json_data["lights"])
    r = requests.put(full_addr, data=json_data)
    print(r.text)

if __name__ == "__main__":
    main()
