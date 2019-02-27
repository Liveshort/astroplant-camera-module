"""
Implementation for the Pi Camera Noir V2.1
Should be similar for other camera's connected to the CSI interface on the Raspberry Pi
"""

import time
import asyncio
import abc
import os
import json

from .camera_commands import *
from .growth_light_control import *
from .debug_print import *

class Camera(object):
    def __init__(self, *args, pi, light_pins, growth_light_control, **kwargs):
        """
        Initialize an object that contains the visible routines.
        Link the pi and gpio pins necessary and provide a function that controls the growth lighting.

        :param pi: link to the pi that controls the lighting
        :param light_pins: dict containing the pin number of the white, red and green pin
        :param growth_light_control: function that can turn the growth lighting on or off
        """

        self.CAM_ID = 0
        self.VIS_CAPABLE = False
        self.NIR_CAPABLE = False
        self.CALIBRATED = False

        self.pi = pi
        self.light_pins = light_pins
        self.growth_light_control = growth_light_control
        self.camera_cfg = dict()

    def do(self, command: CameraCommandType):
        if command == CameraCommandType.REGULAR_PHOTO and self.VIS_CAPABLE:
            return self.vis.regular_photo()
        elif command == CameraCommandType.LEAF_MASK and self.VIS_CAPABLE:
            return self.vis.leaf_mask()
        else:
            d_print("Camera does not support command '{}', returning empty...", 3)
            return ""

    @abc.abstractmethod
    def capture_image_auto(self, path_to_img):
        raise NotImplementedError()

    @abc.abstractmethod
    def capture_image(self, path_to_img):
        raise NotImplementedError()

    def calibrate(self):
        """
        Calibrates the camera and the light sources.
        """

        # turn off the growth lighting
        d_print("Turning off growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.OFF)

        if self.VIS_CAPABLE:
            self.calibrate_crop()
            self.calibrate_white()
        if self.NIR_CAPABLE:
            self.calibrate_nir()

    def calibrate_crop(self):
        # turn on the white light
        d_print("Turning on white camera lighting...", 1)
        self.pi.write(self.light_pins["white"], 1)
        time.sleep(1)

        # ask user to put something pointing somewhere in the kit
        print("Please put something which you can identify pointing somewhere inside the kit (example: pen) and close the kit.")
        print("Type anything to continue.")
        rsp = input("Input:")

        # take photo in auto
        print("Taking auto photo...")
        path_to_img = "{}/img/{}.jpg".format(os.getcwd(), "auto")
        self.capture_image_auto(path_to_img)
        print("An auto photo was taken and saved at {}.\n".format(path_to_img))

        # ask user for correct orientation
        print("For ease of use, we would like the photos to be oriented with the opening of the kit at the bottomside.")
        print("Please select the correct orientation for your camera:")
        print("    0:   correctly oriented")
        print("    90:  opening is on the right side (image will be rotated clockwise)")
        print("    180: opening is on the top side (image will be flipped)")
        print("    270: opening is on the left side (image will be rotated counterclockwise)")
        self.camera_cfg["rotation"] = input("Input: ")

        # make confirmation photo
        print("Taking auto photo...")
        path_to_img = "{}/img/{}.jpg".format(os.getcwd(), "oriented")
        self.capture_image_auto(path_to_img)
        print("An automatic photo was taken and saved at {}.\n".format(path_to_img))

        print("Now we would like to crop the photo to the size of the bottom plate of the kit.")
        print("Open up your favorite image editor (paint should suffice) and find the pixel values (top left is (0,0)) for the following:")
        self.camera_cfg["x_min"] = input("(x) position of the left border of the bottom plate:   ")
        self.camera_cfg["x_max"] = input("(x) position of the right border of the bottom plate:  ")
        self.camera_cfg["y_min"] = input("(y) position of the top border of the bottom plate:    ")
        self.camera_cfg["y_max"] = input("(y) position of the bottom border of the bottom plate: ")

    def calibrate_white(self):
        # turn on the white light
        d_print("Turning on white camera lighting...", 1)
        self.pi.write(self.light_pins["white"], 1)
        time.sleep(1)

    def calibrate_nir(self):
        raise NotImplementedError()

    def state(self):
        """
        Prints the current state of the camera.
        """

        print("\nCamera properties:")
        print("    CAM_ID:       {}".format(self.CAM_ID))
        print("    VIS_CAPABLE:  {}".format(self.VIS_CAPABLE))
        print("    NIR_CAPABLE:  {}".format(self.NIR_CAPABLE))
        print("    CALIBRATED:   {}".format(self.CALIBRATED))

        print("\nConnections:")
        print("    pi:           {}".format(self.pi))
        print("    light pins:   {}".format(self.light_pins))
        print("    growth light: {}".format(self.growth_light_control))

        print("")

    def sanity_check(self):
        """
        Performs a check on the parameters supplied to the camera. Also lists basic information.
        """

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
