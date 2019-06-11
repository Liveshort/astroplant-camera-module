"""
Implementation of the camera parent object.
General mechanics are implemented in this file.
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
from astroplant_camera_module.setup import check_directories

class CAMERA(object):
    def __init__(self, *args, light_control, working_directory, **kwargs):
        """
        Initilize the parent camera object. Most of the routines are specified here, as well as the command tree of what to do with commands received from the user. Initializes some variables to a dummy state, which need to be overwritten explicitly by the child camera.

        :param light_control: function that allows control over the lighting. Parameters are the channel to control and either a 0 or 1 for off and on respectively
        :param light_channels: list containing allowable light channels
        """

        self.CAM_ID = 0
        self.NDVI_CAPABLE = False
        self.HAS_UPDATE = False
        self.CALIBRATED = False

        self.light_control = light_control
        self.working_directory = working_directory

        # check and set up the necessary directories
        check_directories(self.working_directory)


    def do(self, command: CC):
        """
        Function that directs the commands from the user to the right place. Does some preliminary checks to see if actions are allowed in the current state of the camera (uncalibrated etc.). Throws an error on the command line if actions are illegal.

        :param command: (C)amera (C)ommand, what the user wants to do.
        """

        if command == CC.WHITE_PHOTO and LC.WHITE in self.light_channels and self.CALIBRATED:
            return self.photo(LC.WHITE)
        elif command == CC.NDVI_PHOTO and self.NDVI_CAPABLE and self.CALIBRATED:
            return self.ndvi.ndvi_photo()
        elif command == CC.GROWTH_PHOTO and LC.GROWTH in self.light_channels and self.CALIBRATED:
            return self.photo(LC.GROWTH)
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


    def save_config_to_file(self):
        """
        Save camera configuration to file.
        """

        with open("{}/cam/cfg/config.json".format(self.working_directory), 'w') as f:
            json.dump(self.config, f, indent=4, sort_keys=True)


    def load_config_from_file(self):
        """
        Load camera configuration from file.
        """

        with open("{}/cam/cfg/config.json".format(self.working_directory), 'r') as f:
            self.config = json.load(f)


    def photo(self, channel: LC):
        """
        Make a photo with the specified light channel and save the image to disk

        :param channel: channel of light a photo needs to be taken from
        :return: path to the photo taken
        """

        # capture a photo of the appropriate channel
        rgb, _ = self.capture(channel)

        # catch error
        if rgb is None:
            res = dict()
            res["contains_photo"] = False
            res["contains_value"] = False
            res["encountered_error"] = True
            res["timestamp"] = curr_time

            return res

        # crop the sensor readout
        rgb = rgb[self.settings.crop["y_min"]:self.settings.crop["y_max"], self.settings.crop["x_min"]:self.settings.crop["x_max"], :]

        # write image to file using imageio's imwrite
        d_print("Writing to file...", 1)
        curr_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        path_to_img = "{}/cam/img/{}_{}.jpg".format(self.working_directory, channel, curr_time)
        imwrite(path_to_img, rgb)

        res = dict()
        res["contains_photo"] = True
        res["contains_value"] = False
        res["encountered_error"] = False
        res["timestamp"] = curr_time
        res["photo_path"] = [path_to_img]
        res["photo_kind"] = [channel]

        return(res)


    def calibrate(self):
        """
        Calibrates the camera and the light sources.
        """

        # ask user to put something white and diffuse in the kit
        d_print("Assuming a white diffuse surface is placed at the bottom of the kit...", 1)

        self.CALIBRATED = False

        # set up the camera config dict
        self.config = dict()
        self.config["cam_id"] = self.CAM_ID
        self.config["rotation"] = 0
        self.config["wb"] = dict()
        self.config["ff"] = dict()
        self.config["ff"]["gain"] = dict()
        self.config["ff"]["value"] = dict()

        d_print("Starting calibration...", 1)

        # calibrate all white balances
        for channel in self.light_channels:
            self.calibrate_white_balance(channel)
        # calibrate the gains
        for channel in self.light_channels:
            if channel == LC.RED or channel == LC.NIR:
                self.calibrate_flatfield_gains(channel)

        # write the configuration to file
        self.save_config_to_file()

        self.CALIBRATED = True


    def calibrate_flatfield_gains(self, channel: LC):
        """
        Calibrate the flatfield of the given channel. A reference value is needed for calculations of for example NDVI. This function computes the average value of the flatfield and saves it with the accompanying gain.

        :param channel: channel of light that requires flatfield calibration
        """

        # capture a photo of the appropriate channel
        rgb, gain = self.capture(channel)

        # save the flatfield gain to the config
        self.config["ff"]["gain"][channel] = float(gain)

        # cut image to size
        rgb = rgb[self.settings.crop["y_min"]:self.settings.crop["y_max"], self.settings.crop["x_min"]:self.settings.crop["x_max"], :]

        # turn rgb into hsv and extract the v channel as the mask
        v = self.extract_value_from_rgb(channel, rgb)
        # get the average intensity of the light and save for flatfielding
        self.config["ff"]["value"][channel] = np.mean(v[self.settings.ground_plane["y_min"]:self.settings.ground_plane["y_max"], self.settings.ground_plane["x_min"]:self.settings.ground_plane["x_max"]])
        d_print("{} ff std: ".format(channel) + str(np.std(v[self.settings.ground_plane["y_min"]:self.settings.ground_plane["y_max"], self.settings.ground_plane["x_min"]:self.settings.ground_plane["x_max"]])), 1)

        # write image to file using imageio's imwrite
        path_to_img = "{}/cam/cfg/{}_mask.jpg".format(self.working_directory, channel)
        d_print("Writing to file...", 1)
        imwrite(path_to_img, rgb.astype(np.uint8))


    def extract_value_from_rgb(self, channel: LC, rgb):
        """
        Subfunction used to extract the right value matrix from the rgb image.

        :param channel: channel of light of which the value matrix is needed
        :param rgb: rgb matrix (original photo)
        :return: value matrix
        """

        if channel == LC.NIR:
            # turn rgb into hsv and extract the v channel as the mask
            hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
            v = hsv[:,:,2]
        elif channel == LC.RED:
            # extract the red channel
            v = rgb[:,:,0]
        else:
            d_print("unknown channel {}, cannot extract value, returning black matrix...".format(channel), 3)
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
        print("    light control:   {}".format(self.light_control))
        print("    light channels:  {}".format(self.light_channels))
        print("    settings:        {}".format(self.settings))

        print("")
