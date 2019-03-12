import asyncio
import pigpio

from cam.camera_commands import *
from cam.debug_print import *
from pi_cam_noir_v21 import *

def growth_light_control_dummy(gl_state):
    d_print("New growth light state: {}".format(gl_state), 1)

if __name__ == "__main__":
    pi = pigpio.pi()
    light_pins = {
        "flood-white": 2,
        "red": 3,
        "nir": 4,
        "spot-white": 17,
        "yellow": 27,
        "blue": 22,
        "green": 10
    }
    gwl = growth_light_control_dummy

    # set all lights to zero
    for key, val in light_pins.items():
        pi.write(val, 0)

    cam = PI_CAM_NOIR_V21(pi = pi, light_pins = light_pins, growth_light_control = gwl)

    cam.do(CameraCommandType.CALIBRATE)
    print(cam.do(CameraCommandType.DEPTH_MAP))
    print(cam.do(CameraCommandType.REGULAR_PHOTO))
    print(cam.do(CameraCommandType.NDVI_PHOTO))

    cam.state()
    cam.sanity_check()
