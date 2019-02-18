import asyncio
import pigpio

from visible_routines import *
from camera_commands import *
from debug_print import *
from pi_cam_noir_v21 import *

def growth_light_control_dummy(gl_state):
    d_print("New growth light state: {}".format(gl_state))

if __name__ == "__main__":
    pi = pigpio.pi()
    light_pins = {
        "white": 4,
        "red": 17
    }
    gwl = growth_light_control_dummy

    cam = PI_CAM_NOIR_V21(pi = pi, light_pins = light_pins, growth_light_control = gwl)

    print(cam.make_photo_vis(CameraCommandType.REGULAR_PHOTO))
