#!/usr/bin/env python3
"""
Automated controller for lights.

Timers are stored in the file pointed to by LIGHT_TIMERS


Use cron or equivalent to have this program automatically run at startup
"""
from lightStripLib import Room
from datetime import datetime
from time import sleep
import sys
import subprocess

TIMER_FILE = "light.transition"  # "light_timers.csv"


def usage(status):
    """Output a help statement for the program."""
    print("""
Elgato Light Controller
    USAGE python3 controller.py [FLAGS]

    -l LOG_FILE     change location of log file
    -q              turn off logging

    """)
    sys.exit(status)


def get_timers(timer_file):
    """
    Return a list of timers.

        Timers read from LIGHT_TIMERS file
        Raw file should read:
        TIME,first element in the scene],second element in the scene, etc
        where '|' is used to separate individual components of each scene element

        for example:
        TIME,HUE|SATURATION|BRIGHTNESS|DURATION|TRANSITION,HUE|SATURATION|BRIGHT...

        On failure, the function returns `timers` in its current state
    """
    timers = [] # list of timers
                # each timer is a tuple consisting of (TIME, TRANSITION, ACTIVATED, LIGHTS)
                # where the time is HHMM in 24 hour time and TRANSITION is a list of tuples
                # each transition tuple consists of (HUE, SATURATION, BRIGHTNESS, DURATION, TRANSITION)
                # where HUE, SATURATION, and BRIGHTNESS are floats and DURATION, TRANSITION are integers
                # representing the DURATION and TRANSITION length of each part of the scene in miliseconds
    with open(timer_file, 'r') as timer_file:
        for raw_timer in timer_file:
            raw_input = raw_timer.split(',')
            time = 0000
            try:
                time = int(raw_input.pop(0))
            except Exception:
                print("failed to parse time:", time)
                return timers
            lights = []
            try:
                lights = [l for l in raw_input.pop(0).split('|') if l]
            except Exception:
                print("failed to parse lights")
                return timers
            scene_elements = []
            while raw_input:
                scene_element = raw_input.pop(0).split('|')
                try:
                    scene_elements.append((
                        float(scene_element[0]),
                        float(scene_element[1]),
                        float(scene_element[2]),
                        int(scene_element[3]),
                        int(scene_element[4])))
                except Exception:
                    print("failed to parse scene element:", scene_element)
                    return timers
            # time to activate, elements, bool if the timer has been activated today, lights to be activated
            timers.append((time, scene_elements, False, lights))
    return timers


def check_file(file: str, old_hash: str, MODE="quiet", output_file: str = "stdout") -> bool:
    """Check if a file changed."""
    new_hash = subprocess.run(
        ['md5sum', file.encode('utf-8')],
        stdout=subprocess.PIPE).stdout.decode('utf-8')
    if old_hash != new_hash:
        log(
            "checking for timers because timer file got modified",
            MODE,
            output_file)
    return new_hash


def log(message, MODE="quiet", output_file: str = "stdout"):
    """Log the message in the appropriate place."""
    if MODE != "quiet":
        if MODE or output_file == "stdout":
            print(message)
        else:
            out = open(output_file, 'a')
            out.write(
                message)
            out.close()


def main():
    """Run the program."""
    LOG_FILE = "controller-log.log"
    MODE = "normal"
    # TODO: make this program respond to command line args
    args = sys.argv[1:]
    while args:
        current_arg = args.pop(0)
        if current_arg == "-l":
            try:
                LOG_FILE = args.pop(0)
            except Exception:
                usage(1)
        if current_arg == '-q':
            MODE = "quiet"
        else:
            usage(1)

    # get hash
    current_hash = subprocess.run(
        ['md5sum', TIMER_FILE],
        stdout=subprocess.PIPE).stdout.decode('utf-8')

    timers = get_timers(TIMER_FILE)   # get all the timers
    # TODO: sort the timers
    room = Room()
    if not room.setup():            # get all the lights
        usage(1)

    log(",".join(timers), MODE, LOG_FILE)

    while True:  # make sure the timer never stops running
        if not timers:
            # if there are no timers, we are just going to stop the program
            sys.exit(1)
        current_time = int(datetime.now().strftime('%H%M'))
        if current_time % 5 == 0:
            log(f"{current_time} - timers: {len(timers)}\n", MODE, LOG_FILE)
            for t in timers:
                time, transition, activated, lights = t
                log(f"\t{time} : {'done' if activated else 'waiting'}\n", MODE, LOG_FILE)
        for index, timer in enumerate(timers):
            time, transition, activated, lights = timer
            if abs(current_time - time) <= 1 and not activated:
                log(f"controller ran: {transition} at {time}\n", MODE, LOG_FILE)
                # run the transition
                if lights:
                    log(f"only transitioning lights: {lights}\n", MODE, LOG_FILE)
                    for light in lights:
                        room.light_transition(light, transition)
                else:
                    log("ran transition on all lights\n", MODE, LOG_FILE)
                    room.room_transition(transition)
                activated = True  # set the timer to activated
            elif current_time <= 1:
                activated = False

            timers[index] = (time, transition, activated, lights)
        sleep(60)  # wait a minute

        # check for any new timers only if the timer file has changed
        new_hash = check_file(TIMER_FILE, current_hash, MODE, LOG_FILE)
        if current_hash != new_hash:
            timers = get_timers(TIMER_FILE)
            current_hash = new_hash
        # and repeat the process


if __name__ == "__main__":
    main()
