#! usr/bin/python3
"""


"""

import sys
import os
import requests
import socket
# Plan: write application for interacting with a application on an embeded system (raspberry pi pico)
# TODO: write C application to run on the raspberry pi pico
# TODO: reverse engineer HTTP requests of elgato lights
# TODO: add docstrings for all functions

# architecture decision: from the perspective of the controller interface, 
# lights might as well not exist as entities with more than a name + color
# from the perspective of the controller they will be ip addresses+port and each 
# will be mapped to a color value at each time
# need to check how much the lights actually want you to send to them, need to see 
# if all of the light data is even necessary


def usage(exitCode: int) -> None:
    progname = os.path.basename(sys.argv[0])
    print(f"""Usage: {progname} [-harpc]
          -h                                Print this message and exit
          -a  TIME [LIGHTS] -o OPTIONS      Add new timer
          -r  TIME                          Remove timer
          -p                                Print out all active timers
          -c  ADDRESS                       Manually set address of the light controller

          TIME is HH:MM in 24 hour time
          LIGHTS is a list of light names
          OPTIONS is a list of integers: ON SATURATION HUE BRIGHTNESS
          """)
    exit(exitCode)

def addTimer(controller_address: str, time: int, lights: list, color: str) -> bool:
    # make an http request to the embedded system to add a new timer
    lightRequest = ",".join(lights) # light names
    response = requests.put(controller_address, data={
        'add': time,
        'lights': lightRequest,
        'color': color
    })
    return True

def removeTimer(controller_address: str, time: int)  -> bool:
    # send request to remove a timer from the list
    response = requests.put(controller_address, data={
        'remove': time
    })
    return True

def printTimers(controller_address: str) -> None:
    # send request to address
    message = requests.get(controller_address)
    # should get back a list of all active timers
    print(message.text)

def findController() -> str: # find the controller
    # use mDNS
    MCAST_GRP = '224.1.1.1'
    MCAST_PORT = 5007
    MULTICAST_TTL = 2
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.bind(MCAST_GRP, MCAST_PORT)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)
    # send message out
    sock.sendto(b'picolightcontroller', (MCAST_GRP, MCAST_PORT))
    # listen for response
    
    # return the address of the controller
    
    return ""

def main():
    arguments = sys.argv[1:]
    while len(arguments) > 0:
        arg = arguments.pop(0)
        match arg:
            case "-h": # help
                usage(0)
            case "-a": # add lights
                if (address := findController() != ""):
                    time = arguments.pop(0) 
                    lights = []
                    raw_options = []
                    while popped := arguments.pop(0) != "-o": # add lights until the -o flag is hit
                        lights.append(popped)
                    while "-" not in (popped := arguments.pop(0)): # add lights until a new flag is hit
                        if "-" in popped: # if we accidentally popped a flag, add it back
                            arguments.insert(0, popped)
                            break
                        raw_options.append(popped)
                    #options = parseOptions(rawOptions) # turn the raw options into a LightOptions object
                    addTimer(address, time, lights, raw_options)
            case "-r":
                if address := findController() != "":
                    removeTimer(arguments.pop(0), address)
            case "-p":
                if address := findController() != "":
                    printTimers(address)
            case _:
                usage(1)
if __name__ == "__main__":
    main()
