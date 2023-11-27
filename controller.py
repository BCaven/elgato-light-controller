#!/usr/bin/env python3
"""
Automated controller for lights

Timers are stored in the file pointed two by LIGHT_TIMERS


Use cron or equivalent to have this program automatically run at startup
"""
from lightStripLib import Room
from datetime import datetime, timedelta
from time import sleep
import sys

LIGHT_TIMERS="light_timers.csv"



def get_timers():
    """
        Return a list of timers

        Timers read from LIGHT_TIMERS file
        Raw file should read:
        TIME,first element in the scene],second element in the scene, etc
        where '|' is used to separate individual components of each scene element

        for example:
        TIME,HUE|SATURATION|BRIGHTNESS|DURATION|TRANSITION,HUE|SATURATION|BRIGHT...

        On failure, the function returns `timers` in its current state
    """
    timers = [] # list of timers
                # each timer is a tuple consisting of (TIME, TRANSITION)
                # where the time is HHMM in 24 hour time and TRANSITION is a list of tuples
                # each transition tuple consists of (HUE, SATURATION, BRIGHTNESS, DURATION, TRANSITION)
                # where HUE, SATURATION, and BRIGHTNESS are floats and DURATION, TRANSITION are integers
                # representing the DURATION and TRANSITION length of each part of the scene in miliseconds
    with open(LIGHT_TIMERS, 'r') as timer_file:
        for raw_timer in timer_file:
            raw_input = raw_timer.split(',')
            time = 0000
            try:
                time = int(raw_input.pop(0))
            except Exception:
                print("failed to parse time:", time)
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
            timers.append((time, scene_elements))
    return timers

def main():
    """
        Main driver for program


    """
    timers = get_timers()   # get all the timers
    # TODO: sort the timers so the earliest timer is first and the latest timer is last
    room = Room()
    room.setup()            # get all the lights

    while True: # make sure the timer never stops running
        if not timers:
            sys.exit(1)
        current_time = int(datetime.now().strftime('%H%M'))
        next_time, next_transition = timers[0]
        latest_time, latest_transition = timers[-1]
        for time, transition in timers:
            if time > current_time and time < next_time: # current_time is some time during the day and time is later that night
                next_time = time
                next_transition = transition
            elif current_time > latest_time: # it is night time and the next timer is the next day
                next_time, next_transition = timers[0]
                break
        # sleep until the next timer happens
        str_time = '0000'
        if next_time > current_time:    # next timer happens in the same day
            str_time = str(next_time - current_time)
        else:                           # next timer happens the next day
            str_time = str(next_time + (2400 - current_time))

        seconds = timedelta(
            hours=int(str_time[:2]),
            minutes=int(str_time[2:])
        ).total_seconds()
        sleep(seconds) # wait until the time is right

        # do the transition
        room.room_transition(next_transition)

        # check for any new timers:
        timers = get_timers()
        # and repeat the process




if __name__ == "__main__":
    main()
