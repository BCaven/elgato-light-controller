#!/usr/bin/python3
"""
Automated controller for lights.

Timers are stored in the file pointed to by LIGHT_TIMERS


Use cron or equivalent to have this program automatically run at startup
"""
from lightStripLib import Room
from timer import Timer
from datetime import datetime
from time import sleep
import sys
import subprocess


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

        TODO: add functionality to "set to a new scene"
            Look at note in lightStripLib.transition_start for more details

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
        file: str,
        old_hash: str,
        MODE="quiet",
        output_file: str = "stdout") -> bool:
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
    """
    Run the main driver for program.

    TODO: make this survive a network failure or change in IP addr
    TODO: script that checks for updates to the main branch and relaunches the controller
    """
    MODE = "verbose"
    LOG_FILE = "controller.log"
    TIMER_FILE = "light.transition"  # "light_timers.csv"
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
        else:
            usage(1)

    # get hash
    current_hash = check_file(TIMER_FILE, "", MODE=MODE, output_file=LOG_FILE)
    timers = get_timers(TIMER_FILE)   # get all the timers
    # TODO: sort the timers
    room = Room()
    if not room.setup():            # get all the lights
        usage(1)

    log(f"timers: {timers}", MODE, LOG_FILE)

    while True:  # make sure the timer never stops running
        if not timers:
            # if there are no timers, we are just going to stop the program
            sys.exit(1)
        current_time = int(datetime.now().strftime('%H%M'))
        if current_time % 5 == 0:
            log(f"{current_time} - timers: {len(timers)}\n", MODE, LOG_FILE)
            for t in timers:
                year, rules, time, lights, transition, end_state, activated = t
                log(
                    f"\t{time} : {'done' if activated else 'waiting'}\n",
                    MODE, LOG_FILE)
        for index, timer in enumerate(timers):
            year, rules, time, lights, transition, end_state, activated = timer
            if abs(current_time - time) <= 1 and not activated:
                log(
                    f"controller ran: {transition} at {time}\n",
                    MODE, LOG_FILE)
                # run the transition
                if lights:
                    log(
                        f"only transitioning lights: {lights}\n",
                        MODE, LOG_FILE)
                    for light in lights:
                        room.light_transition(light, transition)
                else:
                    log("ran transition on all lights\n", MODE, LOG_FILE)
                    room.room_transition(transition, end_scene=end_state)
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
