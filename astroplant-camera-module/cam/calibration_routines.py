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
        # turn on the white light
        d_print("Turning on white camera lighting...", 1)
        self.pi.write(self.light_pins["flood-white"], 1)
        time.sleep(0.1)

        # ask user to put something pointing somewhere in the kit
        print("Please put something which you can identify pointing somewhere inside the kit (e.g.: pen) and close the kit.")
        print("Type anything to continue.")
        rsp = input("Input: ")

        # take photo in auto mode
        print("Taking auto photo...")
        path_to_img = "{}/img/{}.jpg".format(os.getcwd(), "auto")
        self.camera.capture_auto(path_to_img)
        print("An auto photo was taken and saved at {}.\n".format(path_to_img))

        # ask user for correct orientation
        print("For ease of use, we would like the photos to be oriented with the opening of the kit at the bottomside.")
        print("Please select the correct orientation for your camera:")
        print("    0:   correctly oriented")
        print("    90:  opening is on the right side (image will be rotated clockwise)")
        print("    180: opening is on the top side (image will be flipped)")
        print("    270: opening is on the left side (image will be rotated counterclockwise)")
        self.camera.camera_cfg["rotation"] = int(input("Input: "))

        # make confirmation photo
        print("Taking auto photo...")
        path_to_img = "{}/img/{}.jpg".format(os.getcwd(), "oriented")
        self.capture_auto(path_to_img)
        print("An automatic photo was taken and saved at {}.\n".format(path_to_img))

        # turn off the white light
        d_print("Turning off white camera lighting...", 1)
        self.pi.write(self.light_pins["flood-white"], 0)
        time.sleep(0.1)

        print("Now we would like to crop the photo to the size of the bottom plate of the kit.")
        print("Open up your favorite image editor (paint should suffice) and find the pixel values (top left is (0,0)) for the following:")
        self.camera.camera_cfg["x_min"] = int(input("(x) position of the left border of the bottom plate:   "))
        self.camera.camera_cfg["x_max"] = int(input("(x) position of the right border of the bottom plate:  "))
        self.camera.camera_cfg["y_min"] = int(input("(y) position of the top border of the bottom plate:    "))
        self.camera.camera_cfg["y_max"] = int(input("(y) position of the bottom border of the bottom plate: "))

        print("\nCrop configuration complete.")

    def calibrate_white_balance(self):
        # ask user to put something white and diffuse in the kit
        print("Please remove the plant container and place a white diffuse surface on the bottom plate of the kit and close the kit.")
        print("Type anything to continue.")
        rsp = input("Input: ")

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

        # ask user to place object in kit
        place_object_in_kit()

        # capture image in a square rgb array
        set_light = set_light_curry(self.pi, self.light_pins["spot-white"])
        rgb, gain = self.camera.capture_low_noise(set_light, remove_object_from_kit_callback, "spot-white")

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
        # limit the case where values are really low to prevent blow out in dark parts of the image
        v[v < 40] = 40

        # save the value part np array to file so it can be loaded later
        path_to_cfg = "{}/cfg/{}.ff".format(os.getcwd(), "spot-white")
        with open(path_to_cfg, 'wb') as f:
            np.save(f, v)

        # write image to file using imageio's imwrite
        path_to_img = "{}/cfg/{}.jpg".format(os.getcwd(), "spot-white_mask")
        d_print("Writing to file...", 1)
        imwrite(path_to_img, rgb.astype(np.uint8))

    def calibrate_red(self):
        # turn on the red light
        d_print("Turning on red camera lighting...", 1)
        self.pi.write(self.light_pins["red"], 1)
        time.sleep(1)

        # ask user to place object in kit
        place_object_in_kit()

        # capture image in a square rgb array
        set_light = set_light_curry(self.pi, self.light_pins["red"])
        rgb, gain = self.camera.capture_low_noise(set_light, remove_object_from_kit_callback, "red")

        self.camera.camera_cfg["gain"]["red"] = float(gain)

        # turn off the red light
        d_print("Turning off red camera lighting...", 1)
        self.pi.write(self.light_pins["red"], 0)
        time.sleep(0.1)

        # cut to size
        rgb = rgb[self.camera.camera_cfg["y_min"]:self.camera.camera_cfg["y_max"], self.camera.camera_cfg["x_min"]:self.camera.camera_cfg["x_max"], :]

        # extract the red channel
        r = rgb[:,:,0]
        # limit the case where values are really low to prevent blow out in dark parts of the image
        r[r < 40] = 40

        # save the value part np array to file so it can be loaded later
        path_to_cfg = "{}/cfg/{}.ff".format(os.getcwd(), "red")
        with open(path_to_cfg, 'wb') as f:
            np.save(f, r)

        # write image to file using imageio's imwrite
        path_to_img = "{}/cfg/{}.jpg".format(os.getcwd(), "red_mask")
        d_print("Writing to file...", 1)
        imwrite(path_to_img, rgb.astype(np.uint8))

    def calibrate_nir(self):
        # turn on the NIR light
        d_print("Turning on nir camera lighting...", 1)
        self.pi.write(self.light_pins["nir"], 1)
        time.sleep(1)

        # ask user to place object in kit
        place_object_in_kit()

        # capture image in a square rgb array
        set_light = set_light_curry(self.pi, self.light_pins["nir"])
        rgb, gain = self.camera.capture_low_noise(set_light, remove_object_from_kit_callback, "nir")

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
        # limit the case where values are really low to prevent blow out in dark parts of the image
        v[v < 40] = 40

        # save the value part np array to file so it can be loaded later
        path_to_cfg = "{}/cfg/{}.ff".format(os.getcwd(), "nir")
        with open(path_to_cfg, 'wb') as f:
            np.save(f, v)

        # write image to file using imageio's imwrite
        path_to_img = "{}/cfg/{}.jpg".format(os.getcwd(), "nir_mask")
        d_print("Writing to file...", 1)
        imwrite(path_to_img, rgb.astype(np.uint8))
