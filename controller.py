#!/usr/bin/python3
"""
Automated controller for lights.

Timers are stored in the file pointed to by LIGHT_TIMERS


Use cron or equivalent to have this program automatically run at startup
"""
from lightStripLib import Room
from timer import Timer
import sys
import subprocess
import logging
import asyncio
from time import sleep

WINDOWS = sys.platform == "win32"

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def usage(status):
    """Output a help statement for the program."""
    print("""
Elgato Light Controller
    USAGE python3 controller.py [FLAGS]

    -h              display this message
    -l LOG_FILE     change location of log file
    -q              turn off logging
    -t TIMER_FILE   change location of timer file
    """)
    sys.exit(status)


def get_timers(timer_file):
    """
    Return a list of timers.

        Timers read from `timer_file`

        On failure, the function returns `timers` in its current state

        YEAR RANGE, RULESET, ACTIVATION TIME, TRANSITION SCENE, END SCENE

        TODO: search for lights by name/group instead of IP (then convert this to IP addr)

        TODO: update how timers are stored

        Goals:
            date range for activation (oct1st - dec1st)
            days of week to activate (just do a bit representing each day)
            I guess you could also include rules for years (but make this optional)
        current implementation:
            allowed months, allowed days (0-whatever), allowed weekdays (sun, mon, etc), daily activation time

            at start of each day, datetime gets year/month/day/weekday and tags each timer as active or inactive

            for all active timers: do normal daytime stuff


        TODO: when timer goes out of range, delete it from the list of timers (year ranges only)
    """
    timers = []  # list of timers

    with open(timer_file, 'r') as timer_file:
        for raw_timer in timer_file:
            raw_input = raw_timer.split(',')
            # first thing: year range
            raw_year = raw_input.pop(0)

            # second thing: bit mask rules
            raw_rules = raw_input.pop(0).split(" ")
            # third thing: activation time
            activation_time = ""
            try:
                activation_time = int(raw_input.pop(0))
            except Exception:
                logger.error("Failed to parse activation time")

            # fourth thing: lights
            lights = raw_input.pop(0)
            lights = []  # TODO make this usable
            # fourth thing: transition
            raw_transition = raw_input.pop(0).split(';')  # might change this
            transition_elements = []
            while raw_transition:
                scene_element = raw_transition.pop(0).split('|')
                try:
                    transition_elements.append((
                        float(scene_element[0]),
                        float(scene_element[1]),
                        float(scene_element[2]),
                        int(scene_element[3]),
                        int(scene_element[4])))
                except Exception:
                    logger.error("Failed to parse scene element")
                    return timers

            # fifth thing: end state
            raw_end_state = raw_input.pop(0).split(';')  # might change this
            end_elements = []
            while raw_end_state:
                scene_element = raw_end_state.pop(0).split('|')
                try:
                    end_elements.append((
                        float(scene_element[0]),
                        float(scene_element[1]),
                        float(scene_element[2]),
                        int(scene_element[3]),
                        int(scene_element[4])))
                except Exception:
                    logger.error("Failed to parse scene element")
                    return timers
            timers.append(Timer(
                year_range=raw_year,
                rules=raw_rules,
                time=activation_time,
                active_lights=lights,
                transition_scene=transition_elements,
                end_scene=end_elements,
                ))  # add the timer to the list
    return timers


def check_file(filename: str, old_hash: str) -> str:
    """Check if a file changed."""
    if WINDOWS:
        logging.warning("Windows not supported")
        return old_hash
    new_hash = subprocess.run(
        ['md5sum', filename.encode('utf-8')],
        stdout=subprocess.PIPE).stdout.decode('utf-8')
    if old_hash != new_hash:
        logger.info("Checking for timers.")
    return new_hash


def parse_args():
    """Return variables."""
    LOG_FILE = "controller.log"
    TIMER_FILE = "light.transition"
    EXPECTED_NUM_LIGHTS = 3
    # parse args
    arguments = sys.argv[1:]
    while arguments:
        arg = arguments.pop(0)
        if arg == '-h':
            usage(0)
        elif arg == '-l':
            try:
                LOG_FILE = arguments.pop(0)
            except Exception:
                logger.error("Failed to parse arguments")
                usage(1)
        elif arg == '-q':
            logger.setLevel(logging.ERROR)
        elif arg == '-t':
            try:
                TIMER_FILE = arguments.pop(0)
            except Exception:
                logger.error("Failed to parse new TIMER_FILE")
                usage(1)
        elif arg == '-n':
            try:
                EXPECTED_NUM_LIGHTS = int(arguments.pop(0))
            except Exception:
                logger.error("Failed to parse number of expected lights")
                usage(1)
        else:
            usage(1)

    return (LOG_FILE, TIMER_FILE, EXPECTED_NUM_LIGHTS)

def main():
    """
    Run the main driver for program.

    TODO: make this survive a network failure or change in IP addr
    TODO: script that checks for updates to the main branch and relaunches the controller
    """
    LOG_FILE, TIMER_FILE, EXPECTED_NUM_LIGHTS = parse_args()
    
    # Set up file handler for logging
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    logging.getLogger().addHandler(console)
    logging.getLogger().setLevel(logging.DEBUG)

    # get hash
    current_hash = check_file(TIMER_FILE, "")
    # get all the timers
    timers = get_timers(TIMER_FILE)
    logger.info("Timers:")
    for timer in timers:
        logger.info("Time: %s, Transition scene: %s, End scene: %s", 
                    timer.activation_time, timer.transition_scene, timer.end_scene)
    # TODO: sort the timers
    room = Room()
    assert room.setup(), "Failed to set up room"
    logger.info("Lights: %s", ", ".join([light.info['displayName'] for light in room.lights]))
    while True:
        if not timers:
            raise ValueError("Timer list is empty")

        room.cleanup_inactive_services()

        for timer in timers:
            if timer.check_timer():
                transition_scene, end_scene = timer.get_transition()
                room.room_transition_threaded(
                    transition_scene,
                    end_scene=end_scene)
                logger.info("\t%s - Activated", timer.get_activation_time())

        sleep(60)
        # check for any new timers only if the timer file has changed
        new_hash = check_file(TIMER_FILE, current_hash)
        if current_hash != new_hash:
            timers = get_timers(TIMER_FILE)
            current_hash = new_hash
            times = ",".join([str(t.get_activation_time()) for t in timers])
            logger.info("Timers: %s", times)
        # and repeat the process


if __name__ == "__main__":
    #asyncio.run(main())
    main()
