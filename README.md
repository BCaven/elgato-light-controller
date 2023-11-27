# elgato-light-controller

---

Controller for elgato light strips
Primary goal is to add functionality to the lights via the addition of a controller.
The client sends commands to the controller, and the controller takes action as commanded.

## Features:

- Timers
- Transitions

## TODO:

- communication between the client and the controller
- multicast connection between the client and the controller

## The controller:

While the controller could be any computer with a python environment and the appropriate libraries installed,
it was built for a raspberry pi.

## The client:

The client is a program on a separate computer that the user interacts with as an intermediary between the user and the controller.


## Required libraries:

To make use of multicast, this project requires [`zeroconf`](https://python-zeroconf.readthedocs.io/en/latest/index.html)
The library can still work by manually assigning static IP addresses, but at the moment the timer assumes the user has `zeroconf` installed
