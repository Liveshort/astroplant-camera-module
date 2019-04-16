"""
Implementation for the Pi Camera Noir V2.1
Should be similar for other camera's connected to the CSI interface on the Raspberry Pi
"""

import time
import picamera.array
import picamera
import os
import cv2
import numpy as np
import json

from fractions import Fraction
from imageio import imwrite

from astroplant_camera_module.core.camera import CAMERA
from astroplant_camera_module.core.ndvi import NDVI
from astroplant_camera_module.misc.debug_print import d_print
from astroplant_camera_module.typedef import LC
from astroplant_camera_module.setup import check_directories

class PI_CAM_NOIR_V21(CAMERA):
    def __init__(self, *args, light_control, light_channels, **kwargs):
        """
        Initialize an object that contains the visible routines.
        Link the pi and gpio pins necessary and provide a function that controls the growth lighting.

        :param light_control: function that allows control over the lighting. Parameters are the channel to control and either a 0 or 1 for off and on respectively
        :param light_channels: list containing allowable light channels
        """

        # set up the camera super class
        super().__init__(light_control = light_control, light_channels = light_channels)

        # check and set up the necessary directories
        check_directories()

        # give the camera a unique ID per brand/kind/etc, software uses this ID to determine whether the
        # camera is calibrated or not
        self.CAM_ID = 1

        # check if NDVI can be handled by this camera/lighting combination
        if LC.RED in self.light_channels and LC.NIR in self.light_channels:
            self.NDVI_CAPABLE = True

        # load config file and check if it matches the cam id, if so, assume calibrated
        try:
            with open("{}/cam/cfg/cam_config.json".format(os.getcwd()), 'r') as f:
                self.config = json.load(f)
            if self.config["cam_id"] == self.CAM_ID:
                self.CALIBRATED = True
                d_print("Succesfully loaded suitable camera configuration.", 1)
            else:
                self.CALIBRATED = False
                d_print("Found camera configuration file, but contents are not suitable for current camera.", 3)
        except (EnvironmentError, ValueError):
            d_print("No suitable camera configuration file found!", 3)
            self.CALIBRATED = False

        self.resolution = (1632,1216)
        self.framerate = Fraction(10, 3)
        self.shutter_speed = 300000
        self.exposure_mode = "off"
        self.exposure_compensation = 0

        # set up ndvi routines
        self.ndvi = NDVI(camera = self)


    def capture(self, channel: LC):
        """
        Function that captures an image. Sets up the sensor and its settings,
        lets it settle and takes a picture, returns the array to the user.

        :param channel: channel of light in which the photo is taken, used for white balance and gain values
        :param lights_off: function with no parameters that turns off the appropriate light for dark frame capture
        :return: 8 bit rgb array containing the image
        """

        # turn on the light
        self.light_control(channel, 1)

        d_print("Warming up camera sensor...", 1)

        with picamera.PiCamera() as sensor:
            # set up the sensor with all its settings
            sensor.resolution = self.resolution
            sensor.rotation = self.config["rotation"]
            sensor.framerate = self.framerate
            sensor.shutter_speed = self.shutter_speed
            #sensor.iso = self.iso
            sensor.awb_mode = "off"
            sensor.awb_gains = (self.config["wb"][channel]["r"], self.config["wb"][channel]["b"])
            d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain), 1)
            time.sleep(20)
            sensor.exposure_mode = self.exposure_mode
            d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain), 1)

            # save the total gain of the sensor for this photo
            gain = sensor.analog_gain*sensor.digital_gain

            # record camera data to array, also get dark frame
            with picamera.array.PiRGBArray(sensor) as output:
                # capture a lit frame
                output.truncate(0)
                sensor.capture(output, 'rgb')
                d_print("    Captured {}x{} image".format(output.array.shape[1], output.array.shape[0]), 1)
                rgb = np.copy(output.array)

                # turn off the light
                self.light_control(channel, 0)

                # also capture a dark frame
                output.truncate(0)
                sensor.capture(output, 'rgb')
                d_print("    Captured {}x{} image".format(output.array.shape[1], output.array.shape[0]), 1)
                dark = np.copy(output.array)

            # perform dark frame subtraction
            rgb = cv2.subtract(rgb, dark)

        d_print("Done.", 1)

        return (rgb, gain)


    def capture_duo(self, after_exposure_lock_callback, wb_channel_0, wb_channel_1):
        """
        Function that captures an image. Sets up the sensor and its settings,
        lets it settle and takes a picture, returns the array to the user.

        :param set_light: function that when called with 0 as parameter turns off the appropriate lights
            and when called with 1 as parameter turns it back on
        :param after_exposure_lock_callback: function that is called after the exposure is locked, no
            parameters, no return value
        :return: 8 bit rgb array containing the image
        """

        # turn on the light
        self.light_control(LC.RED, 1)

        d_print("Warming up camera sensor...", 1)

        with picamera.PiCamera() as sensor:
            # set up the sensor with all its settings
            sensor.resolution = self.resolution
            sensor.rotation = self.config["rotation"]
            sensor.framerate = self.framerate
            sensor.shutter_speed = self.shutter_speed
            #sensor.iso = self.iso
            sensor.awb_mode = "off"
            sensor.awb_gains = (self.config["wb"][wb_channel_0]["r"], self.config["wb"][wb_channel_0]["b"])
            d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain), 1)
            time.sleep(10)
            sensor.exposure_mode = self.exposure_mode
            d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain), 1)

            # save the total gain of the sensor for this photo
            gain = sensor.analog_gain*sensor.digital_gain

            # do the after exposure lock callback, in case something needs to be performed here
            after_exposure_lock_callback()

            # record camera data to array, also get dark frame
            #rgb = np.zeros((1216,1216,3), dtype=np.uint8)
            #dark = np.zeros((1216,1216,3), dtype=np.uint8)
            with picamera.array.PiRGBArray(sensor) as output:
                # capture a lit frame
                output.truncate(0)
                sensor.capture(output, 'rgb')
                d_print("    Captured {}x{} image".format(output.array.shape[1], output.array.shape[0]), 1)
                rgb_0 = np.copy(output.array)

                # turn off the first light
                self.light_control(LC.RED, 0)

                # capture a dark frame
                output.truncate(0)
                sensor.capture(output, 'rgb')
                d_print("    Captured {}x{} image".format(output.array.shape[1], output.array.shape[0]), 1)
                dark = np.copy(output.array)

                # set new white balance, turn on the second light
                sensor.awb_gains = (self.config["wb"][wb_channel_1]["r"], self.config["wb"][wb_channel_1]["b"])
                self.light_control(LC.NIR, 1)

                # capture the second frame
                output.truncate(0)
                sensor.capture(output, 'rgb')
                d_print("    Captured {}x{} image".format(output.array.shape[1], output.array.shape[0]), 1)
                rgb_1 = np.copy(output.array)

            # turn off the second light
            self.light_control(LC.NIR, 0)

            # perform dark frame subtraction
            rgb_0 = cv2.subtract(rgb_0, dark)
            rgb_1 = cv2.subtract(rgb_1, dark)

        d_print("Done.", 1)

        return (rgb_0, rgb_1, gain)


    def calibrate_white_balance(self, channel: LC):
        """
        Function that calibrates the white balance for certain lighting specified in the channel parameter. This is camera specific, so it needs to be specified for each camera.

        :param channel: light channel that needs to be calibrated
        """

        d_print("Warming up camera sensor...", 1)

        # turn on channel light
        self.light_control(channel, 1)

        if channel == LC.WHITE or channel == LC.NIR:
            with picamera.PiCamera() as sensor:
                # set up the sensor with all its settings
                sensor.resolution = (128, 80)
                sensor.rotation = self.config["rotation"]
                sensor.framerate = self.framerate
                sensor.shutter_speed = self.shutter_speed
                d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain), 1)
                time.sleep(10)
                sensor.exposure_mode = self.exposure_mode
                sensor.awb_mode = "off"
                d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain), 1)

                # set up the blue and red gains
                rg, bg = (1.2, 1.2)
                sensor.awb_gains = (rg, bg)

                # record camera data to array and scale up a numpy array
                #rgb = np.zeros((1216,1216,3), dtype=np.uint16)
                with picamera.array.PiRGBArray(sensor) as output:
                    # capture images and analyze until convergence
                    for i in range(30):
                        output.truncate(0)
                        sensor.capture(output, 'rgb')
                        rgb = np.copy(output.array)

                        #crop = rgb[508:708,666:966,:]
                        crop = rgb[30:50,32:96,:]

                        r, g, b = (np.mean(crop[..., i]) for i in range(3))
                        d_print("\trg: {:4.3f} bg: {:4.3f} --- ({:4.1f}, {:4.1f}, {:4.1f})".format(rg, bg, r, g, b), 1)

                        if abs(r - g) > 1:
                            if r > g:
                                rg -= 0.025
                            else:
                                rg += 0.025
                        if abs(b - g) > 1:
                            if b > g:
                                bg -= 0.025
                            else:
                                bg += 0.025

                        path_to_img = "{}/cam/tst/{}{}.jpg".format(os.getcwd(), "wb", i)
                        imwrite(path_to_img, rgb)

                        sensor.awb_gains = (rg, bg)
        else:
            rg = 1.0
            bg = 1.0

        # turn off channel light
        self.light_control(channel, 0)

        self.config["wb"][channel] = dict()
        self.config["wb"][channel]["r"] = rg
        self.config["wb"][channel]["b"] = bg

        d_print("Done.", 1)
