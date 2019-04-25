import datetime
import os
import time
import cv2

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors

from imageio import imwrite

from astroplant_camera_module.misc.debug_print import d_print
from astroplant_camera_module.typedef import LC


def empty_callback():
    pass


# function used to obtain Polariks ndvi map
def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=100):
    new_cmap = colors.LinearSegmentedColormap.from_list("trunc({n},{a:.2f},{b:.2f})".format(n=cmap.name, a=minval, b=maxval), cmap(np.linspace(minval, maxval, n)))

    return new_cmap


class NDVI(object):
    def __init__(self, *args, camera, **kwargs):
        """
        Initialize an object that contains the NDVI routines. Since this module is an extra module that can be loaded on top of a simple camera that just takes pictures, it is in a seperate file.

        :param camera: link to the camera object controlling these subroutines
        """

        self.camera = camera


    def ndvi_matrix(self):
        """
        Internal function that makes the ndvi matrix from a red and a nir image. Pixel values are compared to the saved values from the calibration earlier in the process.

        :return: ndvi matrix
        """

        # capture images in a square rgb array
        rgb_r, gain_r = self.camera.capture(LC.RED)
        rgb_nir, gain_nir = self.camera.capture(LC.NIR)

        # crop the sensor readout
        rgb_r = rgb_r[self.camera.settings.crop["y_min"]:self.camera.settings.crop["y_max"], self.camera.settings.crop["x_min"]:self.camera.settings.crop["x_max"], :]
        r = rgb_r[:,:,0]

        # apply flatfield mask
        mask = self.camera.config["ff"]["value"]["red"]
        Rr = 0.8*self.camera.config["ff"]["gain"]["red"]/gain_r*np.divide(r, mask)

        # crop the sensor readout
        rgb_nir = rgb_nir[self.camera.settings.crop["y_min"]:self.camera.settings.crop["y_max"], self.camera.settings.crop["x_min"]:self.camera.settings.crop["x_max"], :]
        hsv = cv2.cvtColor(rgb_nir, cv2.COLOR_RGB2HSV)
        v = hsv[:,:,2]

        # apply flatfield mask
        mask = self.camera.config["ff"]["value"]["nir"]
        Rnir = 0.8*self.camera.config["ff"]["gain"]["nir"]/gain_nir*np.divide(v, mask)

        # write image to file using imageio's imwrite
        path_to_img = "{}/cam/tmp/{}.jpg".format(os.getcwd(), "red_raw")
        imwrite(path_to_img, rgb_r.astype(np.uint8))

        path_to_img = "{}/cam/tmp/{}.jpg".format(os.getcwd(), "nir_raw")
        imwrite(path_to_img, rgb_nir.astype(np.uint8))

        d_print("\tred max: " + str(np.amax(Rr)), 1)
        d_print("\tnir max: " + str(np.amax(Rnir)), 1)

        path_to_img = "{}/cam/tmp/{}.jpg".format(os.getcwd(), "red")
        imwrite(path_to_img, np.uint8(255*Rr/np.amax(Rr)))

        path_to_img = "{}/cam/tmp/{}.jpg".format(os.getcwd(), "nir")
        imwrite(path_to_img, np.uint8(255*Rnir/np.amax(Rnir)))

        # finally calculate ndvi (with some failsafes)
        num = Rnir - Rr
        den = Rnir + Rr
        num[np.logical_and(den < 0.05, den > -0.05)] = 0.0
        den[den < 0.05] = 1.0
        ndvi = np.divide(num, den)

        return ndvi


    def ndvi_photo(self):
        """
        Make a photo in the nir and the red spectrum and overlay to obtain ndvi.

        :return: (path to the ndvi image, average ndvi value for >0.25 (iff the #pixels is larger than 2 percent of the total))
        """

        # get the ndvi matrix
        ndvi_matrix = self.ndvi_matrix()
        ndvi_matrix = np.clip(ndvi_matrix, -1.0, 1.0)
        if np.count_nonzero(ndvi_matrix > 0.25) > 0.02*np.size(ndvi_matrix):
            ndvi = np.mean(ndvi_matrix[ndvi_matrix > 0.25])
        else:
            ndvi = 0

        rescaled = np.uint8(np.round(127.5*(ndvi_matrix + 1.0)))

        # set the right colormap
        cmap = plt.get_cmap("nipy_spectral_r")
        Polariks_cmap = truncate_colormap(cmap, 0, 0.6)

        ndvi_plot = np.copy(ndvi_matrix)
        ndvi_plot[ndvi_plot<0.25] = np.nan

        path_to_img = "{}/cam/img/{}{}.jpg".format(os.getcwd(), "ndvi", 2)
        plt.figure(figsize=(12,10))
        plt.imshow(ndvi_plot, cmap=Polariks_cmap)
        plt.colorbar()
        plt.title("NDVI")
        plt.savefig(path_to_img)

        # write image to file using imageio's imwrite
        d_print("Writing to file...", 1)
        curr_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        path_to_img = "{}/cam/img/{}{}.tif".format(os.getcwd(), "ndvi", 1)
        imwrite(path_to_img, rescaled)

        return(path_to_img, ndvi)


    def ndvi(self):
        """
        Make a photo in the nir and the red spectrum and overlay to obtain ndvi.

        :return: average ndvi value
        """

        # get the ndvi matrix
        ndvi_matrix = self.ndvi_matrix()
        ndvi = np.mean(ndvi_matrix[ndvi_matrix > 0.2])

        return(ndvi)
