import pigpio
import time

from astroplant_camera_module.misc.debug_print import d_print
from astroplant_camera_module.typedef import CC, LC
from astroplant_camera_module.cameras.pi_cam_noir_v21 import PI_CAM_NOIR_V21, SETTINGS_V5
from misc import set_all_lights_to_zero

def light_control_curry(pi):
    def light_control(channel: LC, state):
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

    set_all_lights_to_zero(pi)

    # set up parameters for the camera
    light_control = light_control_curry(pi)
    light_channels = [LC.WHITE, LC.RED, LC.NIR]
    settings = SETTINGS_V5()

    cam = PI_CAM_NOIR_V21(light_control = light_control, light_channels = light_channels, settings = settings)

    print(cam.CALIBRATED)
    cam.do(CC.CALIBRATE)
    cam.do(CC.UPDATE)
    print(cam.do(CC.WHITE_PHOTO))
    print(cam.do(CC.NDVI_PHOTO))
    print(cam.do(CC.GROWTH_PHOTO))

    cam.state()
