import asyncio
import pigpio
import time

from cam.camera_commands import CCT
from cam.debug_print import *
from cam.light_channels import LC
from pi_cam_noir_v21 import *

def growth_light_control_dummy(gl_state):
    d_print("New growth light state: {}".format(gl_state), 1)

def light_control_curry(pi):
    def light_control(channel, state):
        d_print("Setting {} camera lighting state to {}".format(channel, state), 1)

        if channel == LC.WHITE:
            pi.write(17, state)
        elif channel == LC.RED:
            pi.write(3, state)
        elif channel == LC.NIR:
            pi.write(4, state)
        else:
            d_print("no such light available", 3)

        time.sleep(0.1)

    return light_control

if __name__ == "__main__":
    pi = pigpio.pi()
    light_pins = {
        "flood-white": 2,
        "red": 3,
        "nir": 4,
        "white": 17,
        "yellow": 27,
        "blue": 22,
        "green": 10
    }
    gwl = growth_light_control_dummy

    light_control = light_control_curry(pi)
    light_channels = [LC.WHITE, LC.RED, LC.NIR]

    # set all lights to zero
    for key, val in light_pins.items():
        pi.write(val, 0)

    cam = PI_CAM_NOIR_V21(pi = pi, light_pins = light_pins, growth_light_control = gwl, light_control = light_control, light_channels = light_channels)

    cam.do(CCT.CALIBRATE)
    print(cam.do(CCT.REGULAR_PHOTO))
    print(cam.do(CCT.NDVI_PHOTO))

    cam.state()
