#! usr/bin/python3
"""Timer class."""


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

    def check_timer(self, time):
        """Check if the timer should be activated."""

    def run_timer(self):
        """Run the timer."""
