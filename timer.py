#! usr/bin/python3
"""Timer class."""

from datetime import datetime


class Timer:
    """Timer class to define timers used by the controller."""

    def __init__(self,
                 year_range,
                 rules,
                 time,
                 active_lights,
                 transition_scene,
                 end_scene):
        """Init the timer."""
        # TODO: add assert statements to make sure everything
        # is the correct type

        self.rules = rules
        self.year_range = year_range
        self.active_lights = active_lights
        self.activation_time = time
        self.transition_scene = transition_scene
        self.end_scene = end_scene
        self.activated = False

    def check_timer(self):
        """
        Check if the timer should be activated.

        Returns Boolean if timer hit, returns None if timer was not activated
        TODO: make a better return system for this
        """
        weekday, month, year, time = tuple(
            datetime.now().strftime('%w-%m-%y-%H%M').split('-'))
        time = int(time)
        # TODO: write check for rules
        return time == self.activation_time and not self.activated

    def get_transition(self):
        """Return transition scene and end scene."""
        return (self.transition_scene, self.end_scene)

    def info(self):
        """Return information about the timer."""
        return (
            self.rules,
            self.year_range,
            self.active_lights,
            self.activation_time,
            self.activated)

    def get_activation_time(self):
        """Return activation time."""
        return self.activation_time

    def is_activated(self):
        """Return bool if activated."""
        return self.activated
