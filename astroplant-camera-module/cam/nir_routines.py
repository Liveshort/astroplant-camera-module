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

class NIR_ROUTINES(object):
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

    def nir_photo(self):
        """
        Make a regular photo using the white lighting connected to the pi.

        :return: path to the photo taken
        """

        # turn off the growth lighting
        d_print("Turning off growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.OFF)

        # capture image in a square rgb array
        set_light = set_light_curry(self.pi, self.light_pins["nir"])
        rgb, _ = self.camera.capture(set_light, empty_callback, "nir")

        # crop the sensor readout
        rgb = rgb[self.camera.camera_cfg["y_min"]:self.camera.camera_cfg["y_max"], self.camera.camera_cfg["x_min"]:self.camera.camera_cfg["x_max"], :]
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)

        # extract value channel
        v = hsv[:,:,2]

        # apply mask
        with open("{}/cfg/{}.ff".format(os.getcwd(), "nir"), 'rb') as f:
            mask = np.load(f)
            v = np.uint8(np.clip(np.round(128*np.divide(v, mask)), 0, 255))

        # write image to file using imageio's imwrite
        d_print("Writing to file...", 1)
        curr_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        path_to_img = "{}/img/{}.tif".format(os.getcwd(), "nir")
        imwrite(path_to_img, v)

        # turn on the growth lighting
        d_print("Turning on growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.ON)

        return(path_to_img)

    def ndvi_photo(self):
        """
        Make a photo and distill a pseudo depth map from it using some cv2 voodoo.

        :return: path to the depth map
        """

        # turn off the growth lighting
        d_print("Turning off growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.OFF)

        # capture images in a square rgb array
        set_light = set_light_curry(self.pi, self.light_pins["red"])
        rgb_r, gain_r = self.camera.capture(set_light, empty_callback, "red")
        set_light = set_light_curry(self.pi, self.light_pins["nir"])
        rgb_nir, gain_nir = self.camera.capture(set_light, empty_callback, "nir")

        # crop the sensor readout
        rgb_r = rgb_r[self.camera.camera_cfg["y_min"]:self.camera.camera_cfg["y_max"], self.camera.camera_cfg["x_min"]:self.camera.camera_cfg["x_max"], :]
        r = rgb_r[:,:,0]

        # apply flatfield mask
        with open("{}/cfg/{}.ff".format(os.getcwd(), "red"), 'rb') as f:
            mask = np.load(f)
            Rr = np.clip(0.8/gain_r*np.divide(r, mask), 0.0, 1.0)

        # crop the sensor readout
        rgb_nir = rgb_nir[self.camera.camera_cfg["y_min"]:self.camera.camera_cfg["y_max"], self.camera.camera_cfg["x_min"]:self.camera.camera_cfg["x_max"], :]
        hsv = cv2.cvtColor(rgb_nir, cv2.COLOR_RGB2HSV)
        v = hsv[:,:,2]

        # apply flatfield mask
        with open("{}/cfg/{}.ff".format(os.getcwd(), "nir"), 'rb') as f:
            mask = np.load(f)
            Rnir = np.clip(0.8/gain_nir*np.divide(v, mask), 0.0, 1.0)

        # finally calculate ndvi
        ndvi = np.divide(Rnir - Rr, Rnir + Rr)
        rescaled = np.uint8(np.round(127.5*(ndvi + 1.0)))
        cm = cv2.applyColorMap(rescaled, cv2.COLORMAP_JET)

        # write image to file using imageio's imwrite
        d_print("Writing to file...", 1)
        curr_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        path_to_img = "{}/img/{}.tif".format(os.getcwd(), "ndvi")
        imwrite(path_to_img, cm)

        # turn on the growth lighting
        d_print("Turning on growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.ON)

        return(path_to_img)
