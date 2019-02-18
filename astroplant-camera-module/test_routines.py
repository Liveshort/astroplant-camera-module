import asyncio
import pigpio

from picamera import PiCamera
from visible_routines import *
from camera_commands import *
from debug_print import *

def growth_light_control_dummy(gl_state):
    d_print("New growth light state: {}".format(gl_state))

if __name__ == "__main__":
    camera = PiCamera()
    pi = pigpio.pi()
    light_pins = {
        "white": 4,
        "red": 17
    }
    gwl = growth_light_control_dummy

    camera.rotation = 180
    camera.resolution = (800,600)

    vis = VISIBLE_ROUTINES(pi = pi, camera = camera, light_pins = light_pins, growth_light_control = gwl)

    print(vis.photo_vis(CameraCommandType.REGULAR_PHOTO))
