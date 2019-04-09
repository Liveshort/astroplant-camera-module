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
from .misc import empty_callback, set_light_curry, place_object_in_kit, remove_object_from_kit_callback
from .light_channels import LC

class CALIBRATION_ROUTINES(object):
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

    def calibrate_crop(self):
        self.camera.camera_cfg["x_min"] = 0
        self.camera.camera_cfg["x_max"] = 1632
        self.camera.camera_cfg["y_min"] = 0
        self.camera.camera_cfg["y_max"] = 1216

        d_print("Crop configuration complete.", 1)

    def calibrate_white_balance(self):
        self.camera.camera_cfg["wb"] = dict()

        for channel in self.light_pins:
            # turn on the white light
            d_print("Turning on camera lighting...", 1)
            self.pi.write(self.light_pins[channel], 1)
            time.sleep(1)

            self.camera.calibrate_white_balance(channel)

            # turn off the white light
            d_print("Turning off camera lighting...", 1)
            self.pi.write(self.light_pins[channel], 0)
            time.sleep(0.1)

    def calibrate_white(self):
        # turn on the white light
        d_print("Turning on white camera lighting...", 1)
        self.pi.write(self.light_pins["spot-white"], 1)
        time.sleep(1)

        # capture image in a square rgb array
        set_light = set_light_curry(self.pi, self.light_pins["spot-white"])
        rgb, gain = self.camera.capture(set_light, empty_callback, "spot-white")

        self.camera.camera_cfg["gain"]["spot-white"] = float(gain)

        # turn off the white light
        d_print("Turning off white camera lighting...", 1)
        self.pi.write(self.light_pins["spot-white"], 0)
        time.sleep(0.1)

        # cut to size
        rgb = rgb[self.camera.camera_cfg["y_min"]:self.camera.camera_cfg["y_max"], self.camera.camera_cfg["x_min"]:self.camera.camera_cfg["x_max"], :]

        # turn rgb into hsv and extract the v channel as the mask
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        v = hsv[:,:,2]
        # get the average intensity of the light and save for flatfielding
        self.camera.camera_cfg["ff"]["spot-white"] = np.mean(v[68:880,428:1240])

        # write image to file using imageio's imwrite
        path_to_img = "{}/cfg/{}.jpg".format(os.getcwd(), "spot-white_mask")
        d_print("Writing to file...", 1)
        imwrite(path_to_img, rgb.astype(np.uint8))

    def calibrate_red(self):
        # turn on the red light
        d_print("Turning on red camera lighting...", 1)
        self.pi.write(self.light_pins["red"], 1)
        time.sleep(1)

        # capture image in a square rgb array
        set_light = set_light_curry(self.pi, self.light_pins["red"])
        rgb, gain = self.camera.capture(set_light, empty_callback, "red")

        self.camera.camera_cfg["gain"]["red"] = float(gain)

        # turn off the red light
        d_print("Turning off red camera lighting...", 1)
        self.pi.write(self.light_pins["red"], 0)
        time.sleep(0.1)

        # cut to size
        rgb = rgb[self.camera.camera_cfg["y_min"]:self.camera.camera_cfg["y_max"], self.camera.camera_cfg["x_min"]:self.camera.camera_cfg["x_max"], :]

        # extract the red channel
        r = rgb[:,:,0]

        # save the value part np array to file so it can be loaded later
        path_to_field = "{}/cfg/{}.field".format(os.getcwd(), "red")
        with open(path_to_field, 'wb') as f:
            np.save(f, r)

        # get the average intensity of the light and save for flatfielding
        self.camera.camera_cfg["ff"]["red"] = np.mean(r[68:880,428:1240])
        print("red ff std: " + str(np.std(r[68:880,428:1240])))

        # write image to file using imageio's imwrite
        path_to_img = "{}/cfg/{}.jpg".format(os.getcwd(), "red_mask")
        d_print("Writing to file...", 1)
        imwrite(path_to_img, rgb.astype(np.uint8))

    def calibrate_nir(self):
        # turn on the NIR light
        d_print("Turning on nir camera lighting...", 1)
        self.pi.write(self.light_pins["nir"], 1)
        time.sleep(1)

        # capture image in a square rgb array
        set_light = set_light_curry(self.pi, self.light_pins["nir"])
        rgb, gain = self.camera.capture(set_light, empty_callback, "nir")

        self.camera.camera_cfg["gain"]["nir"] = float(gain)

        # turn off the nir light
        d_print("Turning off nir camera lighting...", 1)
        self.pi.write(self.light_pins["nir"], 0)
        time.sleep(0.1)

        # cut to size
        rgb = rgb[self.camera.camera_cfg["y_min"]:self.camera.camera_cfg["y_max"], self.camera.camera_cfg["x_min"]:self.camera.camera_cfg["x_max"], :]

        # turn rgb into hsv and extract the v channel as the mask
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        v = hsv[:,:,2]
        # get the average intensity of the light and save for flatfielding
        self.camera.camera_cfg["ff"]["nir"] = np.mean(v[68:880,428:1240])
        print("nir ff std: " + str(np.std(v[68:880,428:1240])))

        # save the value part np array to file so it can be loaded later
        path_to_field = "{}/cfg/{}.field".format(os.getcwd(), "nir")
        with open(path_to_field, 'wb') as f:
            np.save(f, v)

        # write image to file using imageio's imwrite
        path_to_img = "{}/cfg/{}.jpg".format(os.getcwd(), "nir_mask")
        d_print("Writing to file...", 1)
        imwrite(path_to_img, rgb.astype(np.uint8))
