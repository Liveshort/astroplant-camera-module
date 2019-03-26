import asyncio
import pigpio
import datetime
import os
import time
import cv2

import numpy as np
from imageio import imwrite

from .growth_light_control import *
from .debug_print import *
from .misc import empty_callback, set_light_curry

class VISIBLE_ROUTINES(object):
    def __init__(self, *args, pi, light_pins, growth_light_control, **kwargs):
        """
        Initialize an object that contains the visible routines.
        Link the pi and gpio pins necessary and provide a function that controls the growth lighting.

        :param pi: link to the pi that controls the lighting
        :param light_pins: dict containing the pin number of the white, red and green pin
        :param growth_light_control: function that can turn the growth lighting on or off
        """

        self.pi = pi
        self.light_pins = light_pins
        self.growth_light_control = growth_light_control

    def set_camera(self, camera):
        self.camera = camera

    def regular_photo(self):
        """
        Make a regular photo using the white lighting connected to the pi.

        :return: path to the photo taken
        """

        # turn off the growth lighting
        d_print("Turning off growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.OFF)

        # capture image in a square rgb array
        set_light = set_light_curry(self.pi, self.light_pins["flood-white"])
        rgb, gain = self.camera.capture(set_light, empty_callback, "flood-white")

        # crop the sensor readout
        rgb = rgb[self.camera.camera_cfg["y_min"]:self.camera.camera_cfg["y_max"], self.camera.camera_cfg["x_min"]:self.camera.camera_cfg["x_max"], :]

        # write image to file using imageio's imwrite
        d_print("Writing to file...", 1)
        curr_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        path_to_img = "{}/img/{}.tif".format(os.getcwd(), "test")
        imwrite(path_to_img, rgb)

        # turn on the growth lighting
        d_print("Turning on growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.ON)

        return(path_to_img)

    def pseudo_depth_map(self):
        """
        Make a photo and distill a pseudo depth map from it using some cv2 voodoo.

        :return: path to the depth map
        """

        # turn off the growth lighting
        d_print("Turning off growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.OFF)

        # capture image in a square rgb array
        set_light = set_light_curry(self.pi, self.light_pins["spot-white"])
        rgb, gain = self.camera.capture(set_light, empty_callback, "spot-white")

        # crop the sensor readout
        rgb = rgb[self.camera.camera_cfg["y_min"]:self.camera.camera_cfg["y_max"], self.camera.camera_cfg["x_min"]:self.camera.camera_cfg["x_max"], :]
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

        # apply mask
        mask = self.camera.camera_cfg["ff"]["spot-white"]
        hsv[:,:,2] = np.uint8(np.clip(np.round(128*np.divide(hsv[:,:,2], mask)), 0, 255))

        rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

        # write image to file using imageio's imwrite
        d_print("Writing to file...", 1)
        curr_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        path_to_img = "{}/img/{}.tif".format(os.getcwd(), "depth_map")
        imwrite(path_to_img, rgb)

        # turn on the growth lighting
        d_print("Turning on growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.ON)

        return(path_to_img)
