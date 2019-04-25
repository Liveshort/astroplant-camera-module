import time

from astroplant_camera_module.typedef import LC
from astroplant_camera_module.misc.debug_print import d_print

def light_control_dummy(channel: LC, state):
    d_print("light_control dummmy called, passing...", 1)

    time.sleep(0.1)
