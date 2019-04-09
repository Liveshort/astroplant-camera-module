"""
Implementation for the Pi Camera Noir V2.1
Should be similar for other camera's connected to the CSI interface on the Raspberry Pi
"""

import time
import asyncio
import abc
import os
import json
import cv2

import numpy as np
from imageio import imwrite

from .camera_commands import CCT
from .growth_light_control import *
from .debug_print import *
from .light_channels import LC
from .misc import lights_off_curry

class Camera(object):
    def __init__(self, *args, pi, light_pins, growth_light_control, light_control, light_channels, **kwargs):
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
        self.light_control = light_control
        self.light_channels = light_channels

    def do(self, command: CCT):
        if command == CCT.REGULAR_PHOTO and self.VIS_CAPABLE and self.CALIBRATED:
            return self.vis.regular_photo()
        elif command == CCT.DEPTH_MAP and self.VIS_CAPABLE and self.CALIBRATED:
            return self.vis.pseudo_depth_map()
        elif command == CCT.LEAF_MASK and self.NIR_CAPABLE and self.CALIBRATED:
            return self.nir.leaf_mask()
        elif command == CCT.NDVI_PHOTO and self.NIR_CAPABLE and self.CALIBRATED:
            return self.nir.ndvi_photo()
        elif command == CCT.NDVI and self.NIR_CAPABLE and self.CALIBRATED:
            return self.nir.ndvi()
        elif command == CCT.CALIBRATE:
            self.calibrate()
        else:
            d_print("Camera does not support command '{}', is it calibrated? ({}), returning empty...".format(command, self.CALIBRATED), 3)
            return ""

    @abc.abstractmethod
    def capture_auto(self, path_to_img):
        raise NotImplementedError()

    @abc.abstractmethod
    def capture(self, set_light, after_exposure_lock_callback, wb_channel):
        raise NotImplementedError()

    @abc.abstractmethod
    def capture_low_noise(self, set_light, after_exposure_lock_callback, wb_channel):
        raise NotImplementedError()

    @abc.abstractmethod
    def calibrate_white_balance(self, channel):
        raise NotImplementedError()

    def calibrate(self):
        """
        Calibrates the camera and the light sources.
        """

        # ask user to put something white and diffuse in the kit
        d_print("Assuming a white diffuse surface is placed at the bottom of the kit...", 1)

        # set up the camera config dict
        self.camera_cfg = dict()
        self.camera_cfg["cam_id"] = self.CAM_ID
        self.camera_cfg["rotation"] = 0
        self.camera_cfg["wb"] = dict()
        self.camera_cfg["ff"] = dict()
        self.camera_cfg["ff"]["gain"] = dict()
        self.camera_cfg["ff"]["value"] = dict()

        d_print("Starting calibration...", 1)

        if self.VIS_CAPABLE:
            self.calibrate_crop()
            self.calibrate_white_balance()
            self.calibrate_channel(LC.WHITE)
            self.calibrate_channel(LC.RED)
        if self.NIR_CAPABLE:
            self.calibrate_channel(LC.NIR)

        # write the configuration to file
        with open("{}/cfg/cam_config.json".format(os.getcwd()), 'w') as f:
            json.dump(self.camera_cfg, f, indent=4, sort_keys=True)

        self.CALIBRATED = True

    def calibrate_crop(self):
        self.camera_cfg["x_min"] = 0
        self.camera_cfg["x_max"] = 1632
        self.camera_cfg["y_min"] = 0
        self.camera_cfg["y_max"] = 1216

        d_print("Crop configuration complete.", 1)

    def calibrate_channel(self, channel: LC):
        # turn on the light
        self.light_control(channel, 1)

        # set up the function that turns off the light for the dark frame and pass to the capture function
        lights_off = lights_off_curry(channel, self.light_control)
        # capture a photo of the appropriate channel
        rgb, gain = self.capture2(channel, lights_off)

        # save the flatfield gain to the config
        self.camera_cfg["ff"]["gain"][channel] = float(gain)

        # cut image to size
        rgb = rgb[self.camera_cfg["y_min"]:self.camera_cfg["y_max"], self.camera_cfg["x_min"]:self.camera_cfg["x_max"], :]

        # turn rgb into hsv and extract the v channel as the mask
        v = self.extract_value_from_rgb(channel, rgb)
        # get the average intensity of the light and save for flatfielding
        self.camera_cfg["ff"]["value"][channel] = np.mean(v[68:880,428:1240])
        print("{} ff std: ".format(channel) + str(np.std(v[68:880,428:1240])))

        # save the value part np array to file so it can be loaded later
        path_to_field = "{}/cfg/{}.field".format(os.getcwd(), channel)
        with open(path_to_field, 'wb') as f:
            np.save(f, v)

        # write image to file using imageio's imwrite
        path_to_img = "{}/cfg/{}_mask.jpg".format(os.getcwd(), channel)
        d_print("Writing to file...", 1)
        imwrite(path_to_img, rgb.astype(np.uint8))

    def extract_value_from_rgb(self, channel: LC, rgb):
        if channel == LC.NIR or channel == LC.WHITE:
            # turn rgb into hsv and extract the v channel as the mask
            hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
            v = hsv[:,:,2]
        elif channel == LC.RED:
            # extract the red channel
            v = rgb[:,:,0]
        else:
            d_print("unknown channel {}".format(channel), 3)
            v = np.zeros([10, 10])

        return v

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
