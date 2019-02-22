"""
Implementation for the Pi Camera Noir V2.1
Should be similar for other camera's connected to the CSI interface on the Raspberry Pi
"""

import time
import asyncio
import abc

from visible_routines import *
from camera_commands import *
from debug_print import *

class Camera(object):
    def __init__(self, *args, pi, light_pins, growth_light_control, **kwargs):
        """
        Initialize an object that contains the visible routines.
        Link the pi and gpio pins necessary and provide a function that controls the growth lighting.

        :param pi: link to the pi that controls the lighting
        :param light_pins: dict containing the pin number of the white, red and green pin
        :param growth_light_control: function that can turn the growth lighting on or off
        """

        self.VIS_CAPABLE = False
        self.NIR_CAPABLE = False

        self.pi = pi
        self.light_pins = light_pins
        self.growth_light_control = growth_light_control

        self.vis = VISIBLE_ROUTINES(pi = self.pi, light_pins = self.light_pins, growth_light_control = self.growth_light_control)

    def make_photo_vis(self, command: CameraCommandType):
        if command == CameraCommandType.REGULAR_PHOTO:
            return self.vis.regular_photo()
        else:
            return self.vis.leaf_mask()

    @abc.abstractmethod
    def capture_image(self, path_to_img):
        raise NotImplementedError()

    def sanity_check(self):
        print("Basic camera capabilities:\n    VIS_CAPABLE: {}\n    NIR_CAPABLE: {}".format(self.VIS_CAPABLE, self.NIR_CAPABLE))
        if self.VIS_CAPABLE == True:
            try:
                print("White light pin: {}".format(self.light_pins["white"]))
            except KeyError:
                print("ERROR, no white light pin defined in dict light_pins...")

            try:
                print("Red light pin: {}".format(self.light_pins["red"]))
            except KeyError:
                print("ERROR, no red light pin defined in dict light_pins...")

            try:
                print("Green light pin: {}".format(self.light_pins["green"]))
            except KeyError:
                print("ERROR, no green light pin defined in dict light_pins...")
