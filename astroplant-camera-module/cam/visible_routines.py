import asyncio
import pigpio
import datetime
import os
import time

from .growth_light_control import *
from .debug_print import *

class VISIBLE_ROUTINES(object):
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

    def regular_photo(self):
        """
        Make a regular photo using the white lighting connected to the pi.

        :return: path to the photo taken
        """

        # turn off the growth lighting
        d_print("Turning off growth lighting...")
        self.growth_light_control(GrowthLightControl.OFF)

        # turn on the white light
        d_print("Turning on white camera lighting...")
        self.pi.write(self.light_pins["white"], 1)
        time.sleep(1)

        # take photo
        curr_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        path_to_img = "{}/img/{}.tif".format(os.getcwd(), "test")
        self.camera.capture_image(path_to_img)

        # turn off the camera lights
        d_print("Turning off white camera lighting...")
        self.pi.write(self.light_pins["white"], 0)

        # turn on the growth lighting
        d_print("Turning on growth lighting...")
        self.growth_light_control(GrowthLightControl.ON)

        return(path_to_img)

    def leaf_mask():
        pass
