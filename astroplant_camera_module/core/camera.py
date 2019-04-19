"""
Implementation for the Pi Camera Noir V2.1
Should be similar for other camera's connected to the CSI interface on the Raspberry Pi
"""

import time
import datetime
import abc
import os
import json
import cv2

import numpy as np
from imageio import imwrite

from astroplant_camera_module.misc.debug_print import d_print
from astroplant_camera_module.typedef import CC, LC

class CAMERA(object):
    def __init__(self, *args, light_control, light_channels, **kwargs):
        """
        Initialize an object that contains the visible routines.
        Link the pi and gpio pins necessary and provide a function that controls the growth lighting.

        :param pi: link to the pi that controls the lighting
        :param light_pins: dict containing the pin number of the white, red and green pin
        :param growth_light_control: function that can turn the growth lighting on or off
        """

        self.CAM_ID = 0
        self.NDVI_CAPABLE = False
        self.HAS_UPDATE = False
        self.CALIBRATED = False

        self.light_control = light_control
        self.light_channels = light_channels


    def do(self, command: CC):
        if command == CC.REGULAR_PHOTO and LC.WHITE in self.light_channels and self.CALIBRATED:
            return self.photo(LC.WHITE)
        elif command == CC.NDVI_PHOTO and self.NDVI_CAPABLE and self.CALIBRATED:
            return self.ndvi.ndvi_photo()
        elif command == CC.NDVI and self.NDVI_CAPABLE and self.CALIBRATED:
            return self.ndvi.ndvi()
        elif command == CC.NIR_PHOTO and LC.NIR in self.light_channels and self.CALIBRATED:
            return self.photo(LC.NIR)
        elif command == CC.CALIBRATE:
            self.calibrate()
        elif command == CC.UPDATE and self.HAS_UPDATE and self.CALIBRATED:
            self.update()
        else:
            d_print("Camera is unable to perform command '{}', is it calibrated? ({})\n    Run [cam].state() to check current camera and lighting status...\n    Returning empty...".format(command, self.CALIBRATED), 3)
            return ""


    @abc.abstractmethod
    def capture(self, channel):
        raise NotImplementedError()


    @abc.abstractmethod
    def calibrate_white_balance(self, channel):
        raise NotImplementedError()


    @abc.abstractmethod
    def update(self):
        raise NotImplementedError()


    @abc.abstractmethod
    def calibrate_specific(self):
        raise NotImplementedError()


    def save_config_to_file(self):
        """
        Save camera configuration to file.
        """

        with open("{}/cam/cfg/config.json".format(os.getcwd()), 'w') as f:
            json.dump(self.config, f, indent=4, sort_keys=True)


    def load_config_from_file(self):
        """
        Load camera configuration from file.
        """

        with open("{}/cam/cfg/config.json".format(os.getcwd()), 'r') as f:
            self.config = json.load(f)


    def photo(self, channel: LC):
        """
        Make a photo with the specified light channel and save the image to disk

        :return: path to the photo taken
        """

        # capture a photo of the appropriate channel
        rgb, _ = self.capture(channel)

        # crop the sensor readout
        rgb = rgb[self.config["y_min"]:self.config["y_max"], self.config["x_min"]:self.config["x_max"], :]

        # write image to file using imageio's imwrite
        d_print("Writing to file...", 1)
        curr_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        path_to_img = "{}/cam/img/{}.tif".format(os.getcwd(), channel)
        imwrite(path_to_img, rgb)

        return(path_to_img)


    def calibrate(self):
        """
        Calibrates the camera and the light sources.
        """

        # ask user to put something white and diffuse in the kit
        d_print("Assuming a white diffuse surface is placed at the bottom of the kit...", 1)

        # set up the camera config dict
        self.config = dict()
        self.config["cam_id"] = self.CAM_ID
        self.config["rotation"] = 0
        self.config["wb"] = dict()
        self.config["ff"] = dict()
        self.config["ff"]["gain"] = dict()
        self.config["ff"]["value"] = dict()

        d_print("Starting calibration...", 1)

        self.calibrate_crop()
        for channel in self.light_channels:
            self.calibrate_white_balance(channel)
            self.calibrate_flatfield_gains(channel)

        self.calibrate_specific()

        # write the configuration to file
        self.save_config_to_file()

        self.CALIBRATED = True


    def calibrate_crop(self):
        self.config["x_min"] = 0
        self.config["x_max"] = 1632
        self.config["y_min"] = 0
        self.config["y_max"] = 1216

        d_print("Crop configuration complete.", 1)


    def calibrate_flatfield_gains(self, channel: LC):
        # capture a photo of the appropriate channel
        rgb, gain = self.capture(channel)

        # save the flatfield gain to the config
        self.config["ff"]["gain"][channel] = float(gain)

        # cut image to size
        rgb = rgb[self.config["y_min"]:self.config["y_max"], self.config["x_min"]:self.config["x_max"], :]

        # turn rgb into hsv and extract the v channel as the mask
        v = self.extract_value_from_rgb(channel, rgb)
        # get the average intensity of the light and save for flatfielding
        self.config["ff"]["value"][channel] = np.mean(v[68:880,428:1240])
        d_print("{} ff std: ".format(channel) + str(np.std(v[68:880,428:1240])), 1)

        # save the value part np array to file so it can be loaded later
        path_to_field = "{}/cam/cfg/{}.field".format(os.getcwd(), channel)
        with open(path_to_field, 'wb') as f:
            np.save(f, v)

        # write image to file using imageio's imwrite
        path_to_img = "{}/cam/cfg/{}_mask.jpg".format(os.getcwd(), channel)
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
        print("    CAM_ID:        {}".format(self.CAM_ID))
        print("    NDVI_CAPABLE:  {}".format(self.NDVI_CAPABLE))
        print("    HAS_UPDATE:    {}".format(self.HAS_UPDATE))
        print("    CALIBRATED:    {}".format(self.CALIBRATED))

        print("\nConnections:")
        print("    light control:    {}".format(self.light_control))
        print("    light channels:  {}".format(self.light_channels))

        print("")
