import time

from debug_print import *

def capture_image(camera, path_to_img):
    d_print("Warming up camera sensor...")
    camera.start_preview()
    time.sleep(2)
    d_print("Taking photo...")
    camera.capture(path_to_img)
    camera.stop_preview()
