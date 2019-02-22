"""
Implementation for the Pi Camera Noir V2.1
Should be similar for other camera's connected to the CSI interface on the Raspberry Pi
"""

import time
import asyncio
import pigpio
import picamera.array
import picamera
import numpy as np

from fractions import Fraction
from imageio import imwrite

from camera import Camera
from visible_routines import *
from camera_commands import *
from debug_print import *

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

        # set up the camera settings specific to this camera
        self.VIS_CAPABLE = True
        #self.NIR_CAPABLE = True

        self.resolution = (1216,1216)
        self.rotation = 270
        self.framerate = Fraction(1, 2)
        self.shutter_speed = 2000000
        self.iso = 100
        self.exposure_mode = "off"
        self.exposure_compensation = -24

        # pass self to the visible routine
        self.vis.set_camera(self)

    def capture_image(self, path_to_img):
        d_print("Warming up camera sensor...")

        with picamera.PiCamera() as sensor:
            # set up the sensor with all its settings
            sensor.resolution = self.resolution
            sensor.framerate = self.framerate
            sensor.rotation = self.rotation
            sensor.shutter_speed = self.shutter_speed
            sensor.iso = self.iso
            d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain))
            time.sleep(20)
            sensor.exposure_mode = self.exposure_mode
            sensor.exposure_compensation = self.exposure_compensation
            d_print("{} {} {}".format(sensor.exposure_speed, sensor.analog_gain, sensor.digital_gain))

            #sensor.start_preview()

            # record camera data to array and scale up a numpy array
            d_print("Stacking images...")
            rgb = np.zeros((1216,1216,3), dtype=np.uint16)
            with picamera.array.PiRGBArray(sensor) as output:
                for i in range(20):
                    output.truncate(0)
                    sensor.capture(output, 'rgb')
                    d_print('    Captured %dx%d image' % (output.array.shape[1], output.array.shape[0]))
                    rgb += output.array

            # crop the sensor readout
            rgb = rgb[192:1056, 0:832, :]

            # determine maximum and scale to full 16 bit scale
            d_print("Scaling result...")
            max = np.amax(rgb)
            rgb *= pow(2,16)//max - 1

            # write image to file using imageio's imwrite
            d_print("Writing to file...")
            imwrite(path_to_img, rgb)

            #sensor.stop_preview()

        d_print("Done.")
