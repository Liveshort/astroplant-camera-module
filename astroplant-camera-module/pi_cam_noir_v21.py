"""
Implementation for the Pi Camera Noir V2.1
Should be similar for other camera's connected to the CSI interface on the Raspberry Pi
"""

import time
import asyncio
import pigpio

from picamera import PiCamera
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
        self.NIR_CAPABLE = True

        self.camera = PiCamera()
        self.camera.rotation = 180
        self.camera.resolution = (800,600)

        # link the camera to the visible routine
        self.vis.set_camera(self)

    def capture_image(self, path_to_img):
        d_print("Warming up camera sensor...")
        self.camera.start_preview()
        time.sleep(2)
        d_print("Taking photo...")
        self.camera.capture(path_to_img)
        self.camera.stop_preview()
