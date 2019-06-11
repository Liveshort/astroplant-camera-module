import pigpio
import time
import os

from astroplant_camera_module.misc.debug_print import d_print
from astroplant_camera_module.typedef import CC, LC
from astroplant_camera_module.cameras.pi_cam_noir_v21 import PI_CAM_NOIR_V21, SETTINGS_V5
from misc import set_all_lights_to_zero

if __name__ == "__main__":
    pi = pigpio.pi()

    set_all_lights_to_zero(pi)

    # set up parameters for the camera
    settings = SETTINGS_V5()

    cam = PI_CAM_NOIR_V21(settings = settings)

    print(cam.CALIBRATED)
    cam.do(CC.CALIBRATE)
    cam.do(CC.UPDATE)
    print(cam.do(CC.WHITE_PHOTO))
    print(cam.do(CC.NDVI_PHOTO))
    print(cam.do(CC.GROWTH_PHOTO))

    cam.state()
