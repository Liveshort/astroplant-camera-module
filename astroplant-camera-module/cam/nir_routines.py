import asyncio
import pigpio
import datetime
import os
import time
import cv2

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors

from imageio import imwrite

from .growth_light_control import *
from .debug_print import *
from .misc import empty_callback, set_light_curry, truncate_colormap

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
        mask = self.camera.camera_cfg["ff"]["value"]["red"]
        Rr = 0.8*self.camera.camera_cfg["ff"]["gain"]["red"]/gain*np.divide(r, mask)

        # crop the sensor readout
        rgb_nir = rgb_nir[self.camera.camera_cfg["y_min"]:self.camera.camera_cfg["y_max"], self.camera.camera_cfg["x_min"]:self.camera.camera_cfg["x_max"], :]
        hsv = cv2.cvtColor(rgb_nir, cv2.COLOR_RGB2HSV)
        v = hsv[:,:,2]

        # apply flatfield mask
        mask = self.camera.camera_cfg["ff"]["value"]["nir"]
        Rnir = 0.8*self.camera.camera_cfg["ff"]["gain"]["nir"]/gain*np.divide(v, mask)

        # save the value part np array to file so it can be loaded later
        path_to_field = "{}/res/{}.field".format(os.getcwd(), "red")
        with open(path_to_field, 'wb') as f:
            np.save(f, r)
        path_to_field = "{}/res/{}.field".format(os.getcwd(), "nir")
        with open(path_to_field, 'wb') as f:
            np.save(f, v)

        # write image to file using imageio's imwrite
        path_to_img = "{}/img/{}.jpg".format(os.getcwd(), "red_raw")
        imwrite(path_to_img, rgb_r.astype(np.uint8))

        path_to_img = "{}/img/{}.jpg".format(os.getcwd(), "nir_raw")
        imwrite(path_to_img, rgb_nir.astype(np.uint8))

        print("red max: " + str(np.amax(Rr)))
        print("nir max: " + str(np.amax(Rnir)))

        path_to_img = "{}/img/{}.jpg".format(os.getcwd(), "red")
        imwrite(path_to_img, np.uint8(255*Rr/np.amax(Rr)))

        path_to_img = "{}/img/{}.jpg".format(os.getcwd(), "nir")
        imwrite(path_to_img, np.uint8(255*Rnir/np.amax(Rnir)))

        # finally calculate ndvi (with some failsafes)
        num = Rnir - Rr
        den = Rnir + Rr
        num[den < 0.05] = 0.0
        den[den < 0.05] = 1.0
        ndvi = np.divide(num, den)

        return ndvi

    def ndvi_photo(self):
        """
        Make a photo in the nir and the red spectrum and overlay to obtain ndvi.

        :return: (path to the ndvi image, average ndvi value for >0.2)
        """

        # turn off the growth lighting
        d_print("Turning off growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.OFF)

        # get the ndvi matrix
        ndvi_matrix = self.ndvi_matrix()
        ndvi_matrix = np.clip(ndvi_matrix, -1.0, 1.0)
        ndvi = np.mean(ndvi_matrix[ndvi_matrix > 0.2])

        rescaled = np.uint8(np.round(127.5*(ndvi_matrix + 1.0)))

        # set the right colormap
        cmap = plt.get_cmap("nipy_spectral_r")
        Polariks_cmap = truncate_colormap(cmap, 0, 0.6)

        ndvi_plot = np.copy(ndvi_matrix)
        ndvi_plot[ndvi_plot<0] = 0

        path_to_img = "{}/img/{}{}.jpg".format(os.getcwd(), "ndvi", 2)
        plt.figure(figsize=(12,10))
        plt.imshow(ndvi_plot, cmap=Polariks_cmap)
        plt.colorbar()
        plt.title("NDVI")
        plt.savefig(path_to_img)

        # write image to file using imageio's imwrite
        d_print("Writing to file...", 1)
        curr_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        path_to_img = "{}/img/{}{}.tif".format(os.getcwd(), "ndvi", 1)
        imwrite(path_to_img, rescaled)

        # turn on the growth lighting
        d_print("Turning on growth lighting...", 1)
        self.growth_light_control(GrowthLightControl.ON)

        return(path_to_img, ndvi)

    def ndvi(self):
        """
        Make a photo in the nir and the red spectrum and overlay to obtain ndvi.

        :return: average ndvi value
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
