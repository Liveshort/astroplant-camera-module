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
        mask = self.camera.camera_cfg["ff"]["nir"]
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

    def ndvi_matrix(self):
        """
        Internal function that makes the ndvi matrix.

        :return: ndvi matrix
        """

        # capture images in a square rgb array
        set_light_0 = set_light_curry(self.pi, self.light_pins["red"])
        set_light_1 = set_light_curry(self.pi, self.light_pins["nir"])
        rgb_r, rgb_nir, gain = self.camera.capture_duo(set_light_0, set_light_1, empty_callback, "red", "nir")

        # crop the sensor readout
        rgb_r = rgb_r[self.camera.camera_cfg["y_min"]:self.camera.camera_cfg["y_max"], self.camera.camera_cfg["x_min"]:self.camera.camera_cfg["x_max"], :]
        r = rgb_r[:,:,0]

        # apply flatfield mask
        mask = self.camera.camera_cfg["ff"]["red"]
        Rr = 0.8*self.camera.camera_cfg["gain"]["red"]/gain*np.divide(r, mask)

        # crop the sensor readout
        rgb_nir = rgb_nir[self.camera.camera_cfg["y_min"]:self.camera.camera_cfg["y_max"], self.camera.camera_cfg["x_min"]:self.camera.camera_cfg["x_max"], :]
        hsv = cv2.cvtColor(rgb_nir, cv2.COLOR_RGB2HSV)
        v = hsv[:,:,2]

        # apply flatfield mask
        mask = self.camera.camera_cfg["ff"]["nir"]
        Rnir = 0.8*self.camera.camera_cfg["gain"]["nir"]/gain*np.divide(v, mask)

        # write image to file using imageio's imwrite
        path_to_img = "{}/img/{}.jpg".format(os.getcwd(), "red_raw")
        imwrite(path_to_img, rgb_r.astype(np.uint8))

        path_to_img = "{}/img/{}.jpg".format(os.getcwd(), "nir_raw")
        imwrite(path_to_img, rgb_nir.astype(np.uint8))

        path_to_img = "{}/img/{}.jpg".format(os.getcwd(), "red")
        imwrite(path_to_img, np.uint8(255*Rr/np.amax(Rr)))

        path_to_img = "{}/img/{}.jpg".format(os.getcwd(), "nir")
        imwrite(path_to_img, np.uint8(255*Rnir/np.amax(Rnir)))

        # finally calculate ndvi
        ndvi = np.divide(Rnir - Rr, Rnir + Rr)

        return ndvi

    def ndvi_photo(self):
        """
        Make a photo in the nir and the red spectrum and overlay to obtain ndvi.

        :return: path to the ndvi image
        """

        # turn off the growth lighting
        d_print("Turning off growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.OFF)

        # get the ndvi matrix
        ndvi_matrix = self.ndvi_matrix()
        ndvi = np.mean(ndvi_matrix[ndvi_matrix > 0.2])

        ndvi_capped = np.copy(ndvi_matrix)
        ndvi_capped[ndvi_capped < 0.2] = 0.0

        rescaled = np.uint8(np.round(127.5*(np.clip(ndvi_matrix, -1.0, 1.0) + 1.0)))
        rescaled2 = np.uint8(np.round(127.5*(np.clip(ndvi_capped, -1.0, 1.0) + 1.0)))
        cm = cv2.applyColorMap(rescaled, cv2.COLORMAP_JET)
        cm = cv2.cvtColor(cm, cv2.COLOR_BGR2RGB)

        # write image to file using imageio's imwrite
        d_print("Writing to file...", 1)
        curr_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        path_to_img = "{}/img/{}{}.tif".format(os.getcwd(), "ndvi", 1)
        imwrite(path_to_img, rescaled)
        path_to_img = "{}/img/{}{}.tif".format(os.getcwd(), "ndvi", 0)
        imwrite(path_to_img, rescaled2)
        path_to_img = "{}/img/{}{}.tif".format(os.getcwd(), "ndvi", 2)
        imwrite(path_to_img, cm)

        # turn on the growth lighting
        d_print("Turning on growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.ON)

        return(path_to_img, ndvi)

    def ndvi(self):
        """
        Make a photo in the nir and the red spectrum and overlay to obtain ndvi.

        :return: path to the ndvi image
        """

        # turn off the growth lighting
        d_print("Turning off growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.OFF)

        # get the ndvi matrix
        ndvi_matrix = self.ndvi_matrix()
        ndvi = np.mean(ndvi_matrix[ndvi_matrix > 0.2])

        # turn on the growth lighting
        d_print("Turning on growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.ON)

        return(ndvi)
