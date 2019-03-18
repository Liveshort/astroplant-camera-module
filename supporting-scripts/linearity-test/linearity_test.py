import picamera
from picamera import mmal, mmalobj, exc
from picamera.mmalobj import to_rational
import time
import pigpio
import picamera.array
import os
import numpy as np

from fractions import Fraction
from imageio import imwrite

# some gain parameters and corresponding functions
# shamelessly copied over from rwb27 at github (credit where credit is due)
# link: https://gist.github.com/rwb27/a23808e9f4008b48de95692a38ddaa08/
# requires userland library (https://github.com/raspberrypi/userland.git)

MMAL_PARAMETER_ANALOG_GAIN = mmal.MMAL_PARAMETER_GROUP_CAMERA + 0x59
MMAL_PARAMETER_DIGITAL_GAIN = mmal.MMAL_PARAMETER_GROUP_CAMERA + 0x5A

def set_gain(camera, gain, value):
    """Set the analog gain of a PiCamera.

    camera: the picamera.PiCamera() instance you are configuring
    gain: either MMAL_PARAMETER_ANALOG_GAIN or MMAL_PARAMETER_DIGITAL_GAIN
    value: a numeric value that can be converted to a rational number.
    """
    if gain not in [MMAL_PARAMETER_ANALOG_GAIN, MMAL_PARAMETER_DIGITAL_GAIN]:
        raise ValueError("The gain parameter was not valid")
    ret = mmal.mmal_port_parameter_set_rational(cam._camera.control._port,
                                                    gain,
                                                    to_rational(value))
    if ret == 4:
        raise exc.PiCameraMMALError(ret, "Are you running the latest version of the userland libraries? Gain setting was introduced in late 2017.")
    elif ret != 0:
        raise exc.PiCameraMMALError(ret)

def set_analog_gain(camera, value):
    """Set the gain of a PiCamera object to a given value."""
    set_gain(camera, MMAL_PARAMETER_ANALOG_GAIN, value)

def set_digital_gain(camera, value):
    """Set the digital gain of a PiCamera object to a given value."""
    set_gain(camera, MMAL_PARAMETER_DIGITAL_GAIN, value)

# script that will produce images with different exposure times, analog gains, digital gains
# to check for linearity of the cam
if __name__ == "__main__":
    # standard parameters for a decent photo
    resolution = (1216,1216)
    #framerate = Fraction(5, 1)
    #shutter_speed = 200000
    framerate = Fraction(25, 1)
    shutter_speed = 40000
    exposure_mode = "off"
    exposure_compensation = 0
    analog_gain = 3
    digital_gain = 1

    # parameters of the test
    framerates = [Fraction(40,1), Fraction(20,1), Fraction(10,1), Fraction(5,1), Fraction(5,2), Fraction(5,4), Fraction(5,8)]
    shutter_speeds = [25000, 50000, 100000, 200000, 400000, 800000, 1600000]
    analog_gains = [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7]
    digital_gains = [0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 6.5, 7]

    # set up a settings list
    settings = []
    for fr, ss in zip(framerates, shutter_speeds):
        settings.append([fr, ss, analog_gain, digital_gain])
    for ag in analog_gains:
        settings.append([framerate, shutter_speed, ag, digital_gain])
    for dg in digital_gains:
        settings.append([framerate, shutter_speed, 1, dg])

    with open('settings.txt', 'w') as f:
        for i, setting in enumerate(settings):
            f.write("{}: {}\n".format(i, setting))

    # turn on the light
    pi = pigpio.pi()
    pi.write(2, 1)

    # first determine correct white balance
    with picamera.PiCamera() as cam:
        # set up the cam with all its settings
        cam.resolution = resolution
        cam.framerate = framerate
        cam.shutter_speed = shutter_speed

        time.sleep(10)

        cam.exposure_mode = exposure_mode
        cam.awb_mode = "off"

        # set up the blue and red gains
        rg, bg = (1.2, 1.2)
        cam.awb_gains = (rg, bg)

        # record camera data to array and scale up a numpy array
        with picamera.array.PiRGBArray(cam) as output:
            # capture images and analyze until convergence
            for i in range(50):
                output.truncate(0)
                cam.capture(output, 'rgb')
                rgb = np.copy(output.array)

                crop = rgb[508:708,508:708,:]

                r, g, b = (np.mean(crop[..., i]) for i in range(3))
                print("rg: {} bg: {} --- ({}, {}, {})".format(rg, bg, r, g, b))

                if abs(r - g) > 1:
                    if r > g:
                        rg -= 0.015
                    else:
                        rg += 0.015
                if abs(b - g) > 1:
                    if b > g:
                        bg -= 0.015
                    else:
                        bg += 0.015

                cam.awb_gains = (rg, bg)

            awb_gains = (rg, bg)

    rsp = input("place the blocked paper under the light...")

    # then perform the test
    for i, setting in enumerate(settings):
        with picamera.PiCamera() as cam:
            # set up the cam with all its settings
            cam.resolution = resolution
            cam.framerate = setting[0]
            cam.shutter_speed = setting[1]
            set_analog_gain(cam, setting[2])
            set_digital_gain(cam, setting[3])
            cam.awb_mode = "off"
            cam.awb_gains = awb_gains

            print("Current a/d gains: {}, {}".format(cam.analog_gain, cam.digital_gain))
            time.sleep(2)
            print("Current a/d gains: {}, {}".format(cam.analog_gain, cam.digital_gain))

            cam.exposure_mode = exposure_mode

            # get an image from the camera
            with picamera.array.PiRGBArray(cam) as output:
                # capture a lit frame
                output.truncate(0)
                cam.capture(output, 'rgb')
                rgb = np.copy(output.array)
                print("took photo with settings: {}".format(setting))

            path_to_img = "{}/img/{}.jpg".format(os.getcwd(), i)
            imwrite(path_to_img, rgb)

    # turn off the light
    pi.write(2,0)
