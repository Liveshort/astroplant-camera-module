"""
Implementation for the Pi Camera Noir V2.1
Should be similar for other camera's connected to the CSI interface on the Raspberry Pi
"""

import time
import asyncio
import pigpio

from picamera import PiCamera
from visible_routines import *
from camera_commands import *
from debug_print import *

class PI_CAM_NOIR_V21(object):

    VIS_CAPABLE = True
    NIR_CAPABLE = True

    def __init__(self, *args, pi, light_pins, growth_light_control, **kwargs):
        """
        Initialize an object that contains the visible routines.
        Link the pi and gpio pins necessary and provide a function that controls the growth lighting.

        :param pi: link to the pi that controls the lighting
        :param light_pins: dict containing the pin number of the white, red and green pin
        :param growth_light_control: function that can turn the growth lighting on or off
        """

        self.pi = pi
        self.camera = PiCamera()
        self.light_pins = light_pins
        self.growth_light_control = growth_light_control

        self.vis = VISIBLE_ROUTINES(pi = self.pi, camera = self.camera, light_pins = self.light_pins, growth_light_control = self.growth_light_control)

        self.camera.rotation = 180
        self.camera.resolution = (800,600)

    def make_photo_vis(self, command):
        if command == CameraCommandType.REGULAR_PHOTO:
            return self.vis.regular_photo()
        else:
            return self.vis.leaf_mask()


    def sanity_check(self):
        if VIS_CAPABLE == True:
            try:
                print("White light pin: {}".format(self.light_pins["white"]))
            except KeyError:
                print("ERROR, no white light pin defined in dict light_pins...")

            try:
                print("Red light pin: {}".format(self.light_pins["red"]))
            except KeyError:
                print("ERROR, no red light pin defined in dict light_pins...")

            try:
                print("Green light pin: {}".format(self.light_pins["red"]))
            except KeyError:
                print("ERROR, no green light pin defined in dict light_pins...")
