#!/usr/bin/python3
"""
Automated controller for lights.

Timers are stored in the file pointed to by LIGHT_TIMERS


Use cron or equivalent to have this program automatically run at startup
"""
from lightStripLib import Room
from timer import Timer
from time import sleep
import sys
import subprocess
from os.path import isfile


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


def parse_rules(rules: list) -> list:
    """
    Parse the rules of a timer.

    PROBLEM: calendar does not start on same day, each month is a different length, etc
    """
    index = 0
    while rules:
        current_token = rules[index]
        if current_token == '(':
            # grab everything until you reach a ')' and run it through `parse_rules` put the output value in the index of the open paren
            mini_rules = [current_token]
            while rules:
                next_token = rules.pop(index)
                mini_rules.append(next_token)
                if next_token == ')':
                    break
            if mini_rules[-1] != ')':
                print("failed to find closing paren")
                print("buffer", mini_rules)
                return []
            new_token = parse_rules(mini_rules)
            if len(new_token) != 1:
                print("parser returned a list of length != 1 when parsing parens")
                print("returned token:", new_token)
                return []
            rules.insert(index, new_token[0])  # insert the new token in the index of the open paren
        elif current_token == '&':
            # grab the previous and next tokens and compute the new value
            try:
                new_val = rules[index-1] & rules[index+1]
                rules[index - 1] = new_val  # make the prev val the output of the &
                rules.pop(index)  # remove the '&' token
                rules.pop(index)  # remove the second val
                index -= 1
            except Exception:
                print("failed to apply &")
                return []
        elif current_token == '|':
            # grab the previous and next tokens and compute the new value
            try:
                new_val = rules[index-1] | rules[index+1]
                rules[index - 1] = new_val  # make the prev val the output of the |
                rules.pop(index)  # remove the '|' token
                rules.pop(index)  # remove the second val
                index -= 1
            except Exception:
                print("failed to apply |")
                return []
            pass
        elif current_token == '-':
            # calc range
            try:
                start_range = rules[index - 1]
                end_range = rules[index + 1]
                # all of the bits between start_range and end_range should be one
                # find the index of the highest bit of the start of the range and
                # the index of the lowest bit of the end of the range

                # could do a white mask shifted left to the smart & white mask shift left to end of the end range
                # PROBLEM: that would get really weird with days of the week because they do not have a designated "start" and "stop"
            except Exception:
                print("failed to calculate range at index", index)
                return []
        else:
            # hit a val token
            # Do not know if you actually need to do anything with these
            pass


def get_timers(timer_file,
               MODE="quiet",
               LOG_FILE="stdout"):
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
                log("Failed to parse activation time", MODE, LOG_FILE)

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
                    print("failed to parse scene element:", scene_element)
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
                    print("failed to parse scene element:", scene_element)
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


def check_file(
        filename: str,
        old_hash: str,
        MODE="quiet",
        output_file: str = "stdout") -> bool:
    """Check if a file changed."""
    new_hash = subprocess.run(
        ['md5sum', filename.encode('utf-8')],
        stdout=subprocess.PIPE).stdout.decode('utf-8')
    if old_hash != new_hash:
        log(
            "checking for timers.",
            MODE,
            output_file)
    return new_hash


def log(message, MODE="quiet", output_file: str = "stdout"):
    """Log the message in the appropriate place."""
    if MODE != "quiet":
        if MODE == "stdout" or output_file == "stdout":
            print(message)
        else:
            if not isfile(output_file):
                create = open(output_file, 'w')
                create.write("")
                create.close()
            out = open(output_file, 'a')
            message = message + "\n"
            out.write(message)
            out.close()


def parse_args():
    """Return variables."""
    MODE = "verbose"
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
                log("Failed to parse arguments", MODE="stdout")
                usage(1)
        elif arg == '-q':
            MODE = "quiet"
        elif arg == '-t':
            try:
                TIMER_FILE = arguments.pop(0)
            except Exception:
                log("Failed to parse new TIMER_FILE", MODE="stdout")
                usage(1)
        elif arg == '-n':
            try:
                EXPECTED_NUM_LIGHTS = int(arguments.pop(0))
            except Exception:
                log("Failed to parse number of expected lights", MODE="stdout")
                usage(1)
        else:
            usage(1)

    return (MODE, LOG_FILE, TIMER_FILE, EXPECTED_NUM_LIGHTS)


def main():
    """
    Run the main driver for program.

    TODO: make this survive a network failure or change in IP addr
    TODO: script that checks for updates to the main branch and relaunches the controller
    """
    MODE, LOG_FILE, TIMER_FILE, EXPECTED_NUM_LIGHTS = parse_args()
    # get hash
    current_hash = check_file(TIMER_FILE, "", MODE=MODE, output_file=LOG_FILE)
    # get all the timers
    timers = get_timers(TIMER_FILE)
    log("timers:", MODE=MODE, output_file=LOG_FILE)
    for timer in timers:
        log(f"time: {timer.activation_time}", MODE, LOG_FILE)
        log(f"transition scene: {timer.transition_scene}", MODE, LOG_FILE)
        log(f"end scene: {timer.end_scene}", MODE, LOG_FILE)
    # TODO: sort the timers
    room = Room()
    assert room.setup(), "Failed to set up room"
    if EXPECTED_NUM_LIGHTS > len(room.lights):
        room.setup()
    log("Lights:", MODE, LOG_FILE)
    light_names = ", ".join(
        [light.info['displayName'] for light in room.lights])
    log(light_names, MODE, LOG_FILE)


    try:
        while True:
            assert timers, "Timer list is empty"

            for timer in timers:
                if timer.check_timer():
                    transition_scene, end_scene = timer.get_transition()
                    if not room.room_transition(
                            transition_scene,
                            end_scene=end_scene):
                        # run it again with the new lights
                        room.room_transition(
                            transition_scene,
                            end_scene=end_scene)
                        log(f"Timer {timer.get_activation_time()} failed - re-scanned and ran timer again", MODE, LOG_FILE)
                        log("New lights:", MODE, LOG_FILE)
                        light_names = ", ".join(
                            [light.info['displayName'] for light in room.lights])
                        log(light_names, MODE, LOG_FILE)

                    timer.activated = True
                    log(f"\t{timer.get_activation_time()} - Activated",
                        MODE, LOG_FILE)

            sleep(60)
            # check for any new timers only if the timer file has changed
            new_hash = check_file(TIMER_FILE, current_hash, MODE, LOG_FILE)
            if current_hash != new_hash:
                timers = get_timers(TIMER_FILE)
                current_hash = new_hash
                times = ",".join([str(t.get_activation_time()) for t in timers])
                log(f"timers: {times}", MODE, LOG_FILE)
            # and repeat the process
    except Exception as e:
        log("Caught exception:", MODE, LOG_FILE)
        log(str(e), MODE, LOG_FILE)
        log("Exiting program...", MODE, LOG_FILE)
        sys.exit(1)


if __name__ == "__main__":
    main()
