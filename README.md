# elgato-light-controller

---

Controller for elgato light strips

The controller reads a list of timers and executes them at the specified time

> Fun fact: this library has been in continuous operation since December 2023.

## Features:

- Timers
- Transitions

## The controller:

While the controller could be any computer with a python environment and the appropriate libraries installed,
it was built for a raspberry pi.

### Using the controller:

The controller looks for transitions in the file `light.transition` unless otherwise specified.

Each line is a timer of the following format: `__,__,time,lights,transition,end`

`time` is 24 hour time in the format `HHMM`

`lights` is a list of ip addresses separated by a `|`

an example of this is `192.168.86.0.1|123.123.13.1.1`

if `lights` is left blank, the controller will run the transition on all lights.

`transition` and `end` are sets of colors in the following format: `hue|saturation|brightness|duration of color|duration of transition to next color`

each color is separated by a `;`

Both the duration time and transition time are in MS.

hue, saturation, and brightness are `float`s, both times are `int`s.

The first two slots regard features that are still in progress, so they can be left blank because their values have no impact on the controller.

In this release, the transition file can only be modified manually; however, there is no need to restart the controller when modifying the transition file because the controller will automatically reload the file.

Examples of what these .transition files look like can be found in `demo.transition` and `light.transition`

To run the controller, use the command `python3 controller.py` in the project directory.

## Required libraries:

To make use of multicast, this project requires [`zeroconf`](https://python-zeroconf.readthedocs.io/en/latest/index.html)

The library can still work by manually assigning static IP addresses, but at the moment the controller assumes the user has `zeroconf` installed and will be unusable without it.
