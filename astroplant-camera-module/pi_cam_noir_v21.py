"""
Implementation for the Pi Camera Noir V2.1
Should be similar for other camera's connected to the CSI interface on the Raspberry Pi
"""

import time
import asyncio
import pigpio
import picamera.array
import picamera
import os
import numpy as np

from fractions import Fraction
from imageio import imwrite
from scipy.ndimage.filters import gaussian_filter

from cam.camera import *
from cam.visible_routines import *
from cam.camera_commands import *
from cam.debug_print import *

class PI_CAM_NOIR_V21(Camera):
    def __init__(self, *args, pi, light_pins, growth_light_control, **kwargs):
        """
        Initialize an object that contains the visible routines.
        Link the pi and gpio pins necessary and provide a function that controls the growth lighting.

        :param pi: link to the pi that controls the lighting
        :param light_pins: dict containing the pin number of the white, red and green pin
        :param growth_light_control: function that can turn the growth lighting on or off
        """

        # set up the camera super class
        super().__init__(pi = pi, light_pins = light_pins, growth_light_control = growth_light_control)

        # give the camera a unique ID per brand/kind/etc, software uses this ID to determine whether the
        # camera is calibrated or not
        self.CAM_ID = 1

        # set up the camera settings specific to this camera
        self.VIS_CAPABLE = True
        #self.NIR_CAPABLE = True

        # load config file and check if it matches the cam id, if so, assume calibrated
        try:
            with open("{}/cfg/cam_config.json".format(os.getcwd()), 'r') as f:
                self.camera_cfg = json.load(f)
            if self.camera_cfg["cam_id"] == self.CAM_ID:
                self.CALIBRATED = True
            else:
                self.CALIBRATED = False
        except (EnvironmentError, ValueError):
            d_print("No camera configuration file found!", 3)
            self.CALIBRATED = False

        self.resolution = (1216,1216)
        self.framerate = Fraction(4, 3)
        self.shutter_speed = 750000
        self.iso = 200
        self.exposure_mode = "off"
        self.exposure_compensation = 0

        # set up visible visible routines
        self.vis = VISIBLE_ROUTINES(pi = self.pi, light_pins = self.light_pins, growth_light_control = self.growth_light_control)
        # pass self (a camera object) to the visible routine
        self.vis.set_camera(self)

    def capture_image_auto(self, path_to_img):
        """
        Function that captures an image with auto settings. WB will probably be off and
        photo might be dark.

        :param path_to_img: string pointing to the path the img needs to be stored at
        :return: 0 for success
        """

        d_print("Warming up camera sensor...", 1)

        with picamera.PiCamera(resolution = self.resolution) as sensor:
            # record camera data to array and scale up a numpy array
            sensor.exposure_mode = "night"
            sensor.rotation = self.camera_cfg["rotation"]
            sensor.framerate = Fraction(2, 1)
            sensor.shutter_speed = 500000
            time.sleep(20)
            print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain))
            d_print("Taking photo...", 1)
            sensor.capture(path_to_img)

        d_print("Done.", 1)

        return 0

    def capture_image(self, path_to_img):
        """
        Function that captures an image. Sets up the sensor and its settings,
        takes a bunch of pictures, applies corrections and writes to file.

        :param path_to_img: string pointing to the path the img needs to be stored at
        :return: 0 for success
        """

        d_print("Warming up camera sensor...", 1)

        with picamera.PiCamera() as sensor:
            # set up the sensor with all its settings
            sensor.resolution = self.resolution
            sensor.rotation = self.camera_cfg["rotation"]
            sensor.framerate = self.framerate
            sensor.shutter_speed = self.shutter_speed
            #sensor.iso = self.iso
            d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain), 1)
            time.sleep(20)
            sensor.exposure_mode = self.exposure_mode
            sensor.exposure_compensation = self.exposure_compensation
            d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain), 1)

            #sensor.start_preview()

            # record camera data to array and scale up a numpy array
            d_print("Stacking images...", 1)
            rgb = np.zeros((1216,1216,3), dtype=np.uint16)
            with picamera.array.PiRGBArray(sensor) as output:
                for i in range(10):
                    output.truncate(0)
                    sensor.capture(output, 'rgb')
                    d_print("    Captured {}x{} image".format(output.array.shape[1], output.array.shape[0]), 1)
                    rgb += 16*output.array

            # crop the sensor readout
            rgb = rgb[self.camera_cfg["y_min"]:self.camera_cfg["y_max"], self.camera_cfg["x_min"]:self.camera_cfg["x_max"], :]

            # apply mask
            with open("{}/cfg/{}.its".format(os.getcwd(), "white"), 'rb') as f:
                mask = np.load(f)
                mask = np.expand_dims(mask, axis=2)
                rgb = np.multiply(rgb, np.tile(mask, (1,1,3)))
                rgb = np.uint16(np.round(rgb))

            # determine maximum and scale to full 16 bit scale
            d_print("Scaling result...", 1)
            max = np.amax(rgb)
            d_print("rgb max = {}".format(max), 1)
            rgb *= pow(2,16)//max - 1

            # write image to file using imageio's imwrite
            d_print("Writing to file...", 1)
            imwrite(path_to_img, rgb)

            #sensor.stop_preview()

        d_print("Done.", 1)

        return 0

    def capture_intensity_mask(self, path_to_img, path_to_cfg):
        """
        Function that makes an intensity mask. Sets up the sensor and its settings,
        takes a bunch of pictures, applies corrections and writes to file.

        :param path_to_img: string pointing to the path the img needs to be stored at
        :param path_to_cfg: string pointing to the path the mask needs to be stored at
        :return: 0 for success
        """

        d_print("Warming up camera sensor...", 1)

        with picamera.PiCamera() as sensor:
            # set up the sensor with all its settings
            sensor.resolution = self.resolution
            sensor.rotation = self.camera_cfg["rotation"]
            sensor.framerate = self.framerate
            sensor.shutter_speed = self.shutter_speed
            #sensor.iso = self.iso
            d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain), 1)
            time.sleep(20)
            sensor.exposure_mode = self.exposure_mode
            sensor.exposure_compensation = self.exposure_compensation
            d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain), 1)

            #sensor.start_preview()

            # record camera data to array and scale up a numpy array
            d_print("Stacking images...", 1)
            rgb = np.zeros((1216,1216,3), dtype=np.uint16)
            with picamera.array.PiRGBArray(sensor) as output:
                for i in range(10):
                    output.truncate(0)
                    sensor.capture(output, 'rgb')
                    d_print("    Captured {}x{} image".format(output.array.shape[1], output.array.shape[0]), 1)
                    rgb += output.array

            # crop the sensor readout
            rgb = rgb[self.camera_cfg["y_min"]:self.camera_cfg["y_max"], self.camera_cfg["x_min"]:self.camera_cfg["x_max"], :]

            # grayscale the image
            its = np.dot(rgb[...,:3], [0.299, 0.587, 0.114])

            # determine maximum and scale to full 16 bit scale
            d_print("Scaling/blurring/inverting result...", 1)
            its /= np.amax(its)
            its = gaussian_filter(its, sigma=7)
            its = np.divide(np.ones_like(its), its)
            its[its > 5] = 5
            its /= np.amax(its)

            with open(path_to_cfg, 'wb') as f:
                np.save(f, its)

            # write image to file using imageio's imwrite
            d_print("Writing to file...", 1)
            its = 255*its
            imwrite(path_to_img, its.astype(np.uint8))

            #sensor.stop_preview()

        d_print("Done.", 1)

        return 0
