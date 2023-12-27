#!/usr/bin/python3
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


def get_timers(timer_file):
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

            # third thing: transition
            raw_transition = raw_input.pop(0).split(';')  # might change this syntax later
            transition_elements = []
            while raw_transition:
                scene_element = raw_input.pop(0).split('|')
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
            # fourth thing: end state
            raw_end_state = raw_input.pop(0).split(';')  # might change this syntax later
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
            timers.append(())  # add the timer to the list
    return timers


def main():
    """
    Run the main driver for program.

    TODO: make this survive a network failure or change in IP addr
    TODO: script that checks for updates to the main branch and relaunches the controller
    """
    # get hash
    current_hash = subprocess.run(
        ['md5sum', TIMER_FILE],
        stdout=subprocess.PIPE).stdout.decode('utf-8')
    timers = get_timers(TIMER_FILE)   # get all the timers
    # TODO: sort the timers so the earliest timer is first and the latest timer is last
    room = Room()
    if not room.setup():            # get all the lights
        sys.exit(1)
    print(timers)

    while True:  # make sure the timer never stops running
        if not timers:
            # if there are no timers, we are just going to stop the program
            sys.exit(1)
        current_time = int(datetime.now().strftime('%H%M'))
        if current_time % 5 == 0:
            print(f"{current_time} - timers: {len(timers)}")
            for t in timers:
                time, transition, activated, lights = t
                print(f"\t{time} : {'done' if activated else 'waiting'}")

        for index, timer in enumerate(timers):
            time, transition, activated, lights = timer
            if abs(current_time - time) <= 1 and not activated:
                print(f"controller ran: {transition} at {time}")
                # run the transition
                if lights:
                    print(f"only transitioning lights: {lights}")
                    for light in lights:
                        room.light_transition(light, transition)
                else:
                    print("ran transition on all lights")
                    room.room_transition(transition)
                activated = True  # set the timer to activated
            elif current_time <= 1:
                activated = False

            timers[index] = (time, transition, activated, lights)
        sleep(60)  # wait a minute

        # check for any new timers only if the timer file has changed
        new_hash = subprocess.run(
            ['md5sum', TIMER_FILE.encode('utf-8')],
            stdout=subprocess.PIPE).stdout.decode('utf-8')
        if current_hash != new_hash:
            print("checking for timers because timer file got modified")
            timers = get_timers(TIMER_FILE)
        current_hash = new_hash
        # and repeat the process


if __name__ == "__main__":
    main()
