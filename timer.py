#! usr/bin/python3
"""Timer class."""

from datetime import datetime
# TODO: fill in bitmasks
MONTH_LENGTH = {
    "january": 31,
    "feburary": 28,
    "feburary-leap": 29,
    "march": 31,
    "april": 30,
    "may": 31,
    "june": 30,
    "july": 31,
    "august": 31,
    "september": 30,
    "october": 31,
    "november": 30,
    "december": 31
}
WEEKDAYS = {
    "monday", "tuesday", "wednesday", "thursday",
    "friday", "saturday", "sunday"
}

def generate_month_mask(
                        active_month: str, leap: bool = False) -> int:
    """Generate a bitmask for a given month."""
    month_order = ("january", "feburary", "march", "april", "may", "june",
                   "july", "august", "september", "october", "november",
                   "december")
    if leap:
        month_order = ("january", "feburary-leap", "march", "april", "may",
                       "june", "july", "august", "september", "october",
                       "november", "december")
    assert active_month in MONTH_LENGTH, f"Invalid Month: {active_month}"
    mask = ''
    for month in month_order:
        # see if there is a string method that fills these in more efficiently
        if month in active_month:
            # add the month filled in with 1s
            mask += "".join("1" for _ in range(MONTH_LENGTH[month]))
        else:
            # add the month filled in with 0s
            mask += "".join("0" for _ in range(MONTH_LENGTH[month]))
    # return the int that represents the mask
    return int(mask, 2)


def generate_weekday_mask(active_day: str,
                          days_of_the_week: tuple = (
                              "monday", "tuesday", "wednesday", "thursday",
                              "friday", "saturday", "sunday"),
                          year_length: int = 365,
                          start_day: str = "monday"
                          ) -> int:
    """Generate int mask for a specific day of the week."""
    assert active_day in days_of_the_week, f"Invalid Day: {active_day}"
    mask = ''
    days = 0
    shift = False
    # Account for years that do not start on the first day of the week
    # by inserting a partial week to the beginning of
    for day in days_of_the_week:
        if day == start_day:
            shift = True
        if shift:
            mask += '1' if day in active_day else '0'
            days += 1

    while days < year_length:
        for day in days_of_the_week:
            mask += '1' if day in active_day else '0'
            days += 1
            if days >= year_length:
                break

    assert len(mask) == year_length, f"Invalid mask length, len: {len(mask)}"
    return int(mask, 2)


def generate_date_mask(date: int, leap: bool = False) -> int:
    """Generate a mask of a date for every month that has it."""
    month_order = ("january", "feburary", "march", "april", "may", "june",
                   "july", "august", "september", "october", "november",
                   "december")
    if leap:
        month_order = ("january", "feburary-leap", "march", "april", "may",
                       "june", "july", "august", "september", "october",
                       "november", "december")
    assert 0 < date and date < 32, f"Invalid date: {date}"
    mask = ''
    # adjust date for zero-indexed months
    date -= 1
    for month in month_order:
        # see if there is a string method that fills these in more efficiently
        mask += "".join(
            "1" if d == date else "0" for d in range(MONTH_LENGTH[month]))

    # return the int that represents the mask
    return int(mask, 2)


def sub_symbols(rules,
                leap: bool = False,
                year_length: int = 365,
                year_start: str = "monday",
                days_of_the_week: tuple = (
                    "monday", "tuesday", "wednesday", "thursday",
                    "friday", "saturday", "sunday"),
                ) -> list:
    """Change months/days/weekdays to the corresponding bitmask."""
    for index, rule in enumerate(rules):
        try:
            rule = int(rule)
        except Exception:
            # if it isnt an int then it is fine, we just want to convert dates to ints
            pass

        if rule in days_of_the_week:
            rules[index] = generate_weekday_mask(rule,
                                                 year_length = year_length,
                                                 days_of_the_week=days_of_the_week)
        elif rule in MONTH_LENGTH:
            rules[index] = generate_month_mask(rule, leap=leap)

        elif rule is int:
            rules[index] = generate_date_mask(rule, leap=leap)


def parse_rules(rules: list,
                allowed_symbols: list = ["(", ")", "|", "-", "&"]
                ) -> list:
    """
    Parse the rules of a timer.

    PROBLEM: calendar does not start on same day, each month is a different length, etc

    this method is recursive

    replace this with theory implementation found in parse_rules.py
    """
    if len(rules) <= 1:
        return rules[0]
    next_token = rules.pop(0)
    # deal with parens
    if next_token == '(':
        # pop until you reach a close paren and feed that entire thing into
        # a separate parse_rules loop
        # PROBLEM: deal with nested parens
        subrules = []
        subdepth = 0
        subtoken = rules.pop(0)
        while subtoken != ")" and subdepth == 0:
            if subtoken == "(":
                subdepth += 1
            elif subtoken == ")":
                subdepth -= 1

            # add current subtoken to subrules
            if subtoken != ")" and subdepth == 0:
                subrules.append(subtoken)
            # pop next subtoken
            subtoken = rules.pop(0)

        # send the subrules off to a new `parse_rules` instance
        new_token = parse_rules(subrules)
        assert len(new_token) == 1, f"Subparser failed to parse to single value. Returned array: {new_token}"
        new_token = new_token[0]
        assert new_token is int, f"Token is not an int: {new_token}"
        # push the generated token to the front of the rule list
        rules.insert(0, new_token)

    assert next_token is int, f"Invalid next token: {next_token}"
    # peek the token after the current one
    # to make sure it is a valid item
    # aka it has to be in allowed_symbols
    assert rules[0] in allowed_symbols, f"invalid symbol token: {rules[0]}"

    return parse_rules(rules, allowed_symbols)


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
        return time == self.activation_time  # and not self.activated

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
