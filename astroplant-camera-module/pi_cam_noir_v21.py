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
import cv2
import numpy as np

from fractions import Fraction
from imageio import imwrite
from scipy.ndimage.filters import gaussian_filter

from cam.camera import *
from cam.calibration_routines import *
from cam.visible_routines import *
from cam.nir_routines import *
from cam.camera_commands import CCT
from cam.debug_print import *
from cam.light_channels import LC

class PI_CAM_NOIR_V21(Camera):
    def __init__(self, *args, pi, light_pins, growth_light_control, light_control, light_channels, **kwargs):
        """
        Initialize an object that contains the visible routines.
        Link the pi and gpio pins necessary and provide a function that controls the growth lighting.

        :param pi: link to the pi that controls the lighting
        :param light_pins: dict containing the pin number of the white, red and green pin
        :param growth_light_control: function that can turn the growth lighting on or off
        """

        # set up the camera super class
        super().__init__(pi = pi, light_pins = light_pins, growth_light_control = growth_light_control, light_control = light_control, light_channels = light_channels)

        # give the camera a unique ID per brand/kind/etc, software uses this ID to determine whether the
        # camera is calibrated or not
        self.CAM_ID = 1

        # set up the camera settings specific to this camera
        self.VIS_CAPABLE = True
        self.NIR_CAPABLE = True

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

        self.resolution = (1632,1216)
        self.framerate = Fraction(10, 3)
        self.shutter_speed = 300000
        self.iso = 200
        self.exposure_mode = "off"
        self.exposure_compensation = 0

        # set up visible routines
        self.vis = VISIBLE_ROUTINES(pi = self.pi, light_pins = self.light_pins, growth_light_control = self.growth_light_control)
        # pass self (a camera object) to the visible routine
        self.vis.set_camera(self)

        # set up nir routines
        self.nir = NIR_ROUTINES(pi = self.pi, light_pins = self.light_pins, growth_light_control = self.growth_light_control)
        # pass self (a camera object) to the nir routine
        self.nir.set_camera(self)

    def capture_auto(self, path_to_img):
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
            sensor.framerate = Fraction(10, 1)
            sensor.shutter_speed = 100000
            time.sleep(10)
            print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain))
            d_print("Taking photo...", 1)
            sensor.capture(path_to_img)

        d_print("Done.", 1)

        return 0

    def capture2(self, channel: LC, lights_off):
        """
        Function that captures an image. Sets up the sensor and its settings,
        lets it settle and takes a picture, returns the array to the user.

        :param channel: channel of light in which the photo is taken, used for white balance and gain values
        :param lights_off: function with no parameters that turns off the appropriate light for dark frame capture
        :return: 8 bit rgb array containing the image
        """

        d_print("Warming up camera sensor...", 1)

        with picamera.PiCamera() as sensor:
            # set up the sensor with all its settings
            sensor.resolution = self.resolution
            sensor.rotation = self.camera_cfg["rotation"]
            sensor.framerate = self.framerate
            sensor.shutter_speed = self.shutter_speed
            #sensor.iso = self.iso
            sensor.awb_mode = "off"
            sensor.awb_gains = (self.camera_cfg["wb"][channel]["r"], self.camera_cfg["wb"][channel]["b"])
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

                lights_off()

                # also capture a dark frame
                output.truncate(0)
                sensor.capture(output, 'rgb')
                d_print("    Captured {}x{} image".format(output.array.shape[1], output.array.shape[0]), 1)
                dark = np.copy(output.array)

            # perform dark frame subtraction
            rgb = cv2.subtract(rgb, dark)

        d_print("Done.", 1)

        return (rgb, gain)

    def capture(self, set_light, after_exposure_lock_callback, wb_channel):
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
        set_light(1)
        time.sleep(0.1)

        d_print("Warming up camera sensor...", 1)

        with picamera.PiCamera() as sensor:
            # set up the sensor with all its settings
            sensor.resolution = self.resolution
            sensor.rotation = self.camera_cfg["rotation"]
            sensor.framerate = self.framerate
            sensor.shutter_speed = self.shutter_speed
            #sensor.iso = self.iso
            sensor.awb_mode = "off"
            sensor.awb_gains = (self.camera_cfg["wb"][wb_channel]["r"], self.camera_cfg["wb"][wb_channel]["b"])
            d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain), 1)
            time.sleep(20)
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
                rgb = np.copy(output.array)

                # turn off the light
                set_light(0)
                time.sleep(1)

                # also capture a dark frame
                output.truncate(0)
                sensor.capture(output, 'rgb')
                d_print("    Captured {}x{} image".format(output.array.shape[1], output.array.shape[0]), 1)
                dark = np.copy(output.array)

            # perform dark frame subtraction
            rgb = cv2.subtract(rgb, dark)

        d_print("Done.", 1)

        return (rgb, gain)

    def capture_duo(self, set_light_0, set_light_1, after_exposure_lock_callback, wb_channel_0, wb_channel_1):
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
        set_light_0(1)
        time.sleep(0.1)

        d_print("Warming up camera sensor...", 1)

        with picamera.PiCamera() as sensor:
            # set up the sensor with all its settings
            sensor.resolution = self.resolution
            sensor.rotation = self.camera_cfg["rotation"]
            sensor.framerate = self.framerate
            sensor.shutter_speed = self.shutter_speed
            #sensor.iso = self.iso
            sensor.awb_mode = "off"
            sensor.awb_gains = (self.camera_cfg["wb"][wb_channel_0]["r"], self.camera_cfg["wb"][wb_channel_0]["b"])
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
                set_light_0(0)
                time.sleep(0.2)

                # capture a dark frame
                output.truncate(0)
                sensor.capture(output, 'rgb')
                d_print("    Captured {}x{} image".format(output.array.shape[1], output.array.shape[0]), 1)
                dark = np.copy(output.array)

                # set new white balance, turn on the second light
                sensor.awb_gains = (self.camera_cfg["wb"][wb_channel_1]["r"], self.camera_cfg["wb"][wb_channel_1]["b"])
                set_light_1(1)
                time.sleep(0.2)

                # capture the second frame
                output.truncate(0)
                sensor.capture(output, 'rgb')
                d_print("    Captured {}x{} image".format(output.array.shape[1], output.array.shape[0]), 1)
                rgb_1 = np.copy(output.array)

            # turn off the second light
            set_light_1(0)

            # perform dark frame subtraction
            rgb_0 = cv2.subtract(rgb_0, dark)
            rgb_1 = cv2.subtract(rgb_1, dark)

        d_print("Done.", 1)

        return (rgb_0, rgb_1, gain)

    def capture_low_noise(self, set_light, after_exposure_lock_callback, wb_channel):
        """
        Function that makes an intensity mask. Sets up the sensor and its settings,
        takes a bunch of pictures, applies corrections and writes to file.

        :param set_light: function that when called with 0 as parameter turns off the appropriate lights
            and when called with 1 as parameter turns it back on
        :param after_exposure_lock_callback: function that is called after the exposure is locked, no
            parameters, no return value
        :return: 8 bit rgb array containing the image
        """

        # turn on the light
        set_light(1)
        time.sleep(0.1)

        d_print("Warming up camera sensor...", 1)

        with picamera.PiCamera() as sensor:
            # set up the sensor with all its settings
            sensor.resolution = self.resolution
            sensor.rotation = self.camera_cfg["rotation"]
            sensor.framerate = self.framerate
            sensor.shutter_speed = self.shutter_speed
            #sensor.iso = self.iso
            sensor.awb_mode = "off"
            sensor.awb_gains = (self.camera_cfg["wb"][wb_channel]["r"], self.camera_cfg["wb"][wb_channel]["b"])
            d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain), 1)
            time.sleep(10)
            sensor.exposure_mode = self.exposure_mode
            d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain), 1)

            # save the total gain of the sensor for this photo
            gain = sensor.analog_gain*sensor.digital_gain

            # do the after exposure lock callback, in case something needs to be performed here
            after_exposure_lock_callback()

            # record camera data to array and scale up a numpy array
            d_print("Stacking images...", 1)
            rgb = np.zeros((1216,1632,3), dtype=np.uint16)
            dark = np.zeros((1216,1632,3), dtype=np.uint16)
            with picamera.array.PiRGBArray(sensor) as output:
                # capture 10 images in a row to reduce noise
                for i in range(10):
                    output.truncate(0)
                    sensor.capture(output, 'rgb')
                    d_print("    Captured {}x{} image".format(output.array.shape[1], output.array.shape[0]), 1)
                    rgb += output.array

                # turn off the light
                set_light(0)
                time.sleep(1)

                # also capture 10 dark frames
                for i in range(10):
                    output.truncate(0)
                    sensor.capture(output, 'rgb')
                    d_print("    Captured {}x{} image".format(output.array.shape[1], output.array.shape[0]), 1)
                    dark += output.array

            # perform dark frame subtraction
            rgb = cv2.subtract(rgb, dark)

            # scale to 8 bit
            rgb = np.floor_divide(rgb, 10)
            rgb = np.uint8(rgb)

        d_print("Done.", 1)

        return (rgb, gain)

    def calibrate_white_balance(self):
        """
        Function that calibrates the white balance for certain lighting specified in the channel parameter. This is camera specific, so it needs to be specified for each camera.
        """

        d_print("Warming up camera sensor...", 1)

        for channel in self.light_channels:
            # turn on channel light
            self.light_control(channel, 1)

            if channel == LC.WHITE or channel == LC.NIR:
                with picamera.PiCamera() as sensor:
                    # set up the sensor with all its settings
                    sensor.resolution = self.resolution
                    sensor.rotation = self.camera_cfg["rotation"]
                    sensor.framerate = self.framerate
                    sensor.shutter_speed = self.shutter_speed
                    #sensor.iso = self.iso
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

                            crop = rgb[508:708,666:966,:]

                            r, g, b = (np.mean(crop[..., i]) for i in range(3))
                            print("rg: {:4.3f} bg: {:4.3f} --- ({:4.1f}, {:4.1f}, {:4.1f})".format(rg, bg, r, g, b))

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

                            path_to_img = "{}/tst/{}{}.jpg".format(os.getcwd(), "wb", i)
                            imwrite(path_to_img, crop)

                            sensor.awb_gains = (rg, bg)
            else:
                rg = 1.3
                bg = 1.6

            # turn off channel light
            self.light_control(channel, 0)

            self.camera_cfg["wb"][channel] = dict()
            self.camera_cfg["wb"][channel]["r"] = rg
            self.camera_cfg["wb"][channel]["b"] = bg

        d_print("Done.", 1)
