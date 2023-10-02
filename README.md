# elgato-light-controller
Controller for elgato light strips
Primary goal is to add functionality to the lights via the addition of an embedded controller.
The client sends commands to the embedded controller, and the controller takes action as commanded.

## TODO:
- Timers
- Light cycles
- syncing multiple lights to one pattern

## The embedded controller:
This project will use a Raspberry Pi Pico W to act as the controller for the lights

## The client:
The client is a program on a separate computer that the user interacts with as an intermediary between the user and the controller.