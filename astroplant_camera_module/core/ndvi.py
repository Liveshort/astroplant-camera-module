import datetime
import time
import cv2

import numpy as np
import multiprocessing as mp

# set up matplotlib in such a way that it does not require an X server
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors

from imageio import imwrite

from astroplant_camera_module.misc.debug_print import d_print
from astroplant_camera_module.typedef import LC


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

        # if an error is caught upstream, send it downstream
        if rgb_r is None or rgb_nir is None:
            return None

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
        path_to_img = "{}/cam/tmp/{}.jpg".format(self.camera.working_directory, "red_raw")
        imwrite(path_to_img, r.astype(np.uint8))

        path_to_img = "{}/cam/tmp/{}.jpg".format(self.camera.working_directory, "nir_raw")
        imwrite(path_to_img, v.astype(np.uint8))

        #d_print("\tred max: " + str(np.amax(Rr)), 1)
        #d_print("\tnir max: " + str(np.amax(Rnir)), 1)

        #d_print("ground plane red avg: {}".format(np.mean(Rr[self.camera.settings.ground_plane["y_min"]:self.camera.settings.ground_plane["y_max"], self.camera.settings.ground_plane["x_min"]:self.camera.settings.ground_plane["x_max"]])), 1)
        #d_print("ground plane nir avg: {}".format(np.mean(Rnir[self.camera.settings.ground_plane["y_min"]:self.camera.settings.ground_plane["y_max"], self.camera.settings.ground_plane["x_min"]:self.camera.settings.ground_plane["x_max"]])), 1)
        #d_print("nir gain: {} ff value: {} ff gain: {}".format(gain_nir, self.camera.config["ff"]["value"]["nir"], self.camera.config["ff"]["gain"]["nir"]), 1)
        #d_print("red gain: {} ff value: {} ff gain: {}".format(gain_r, self.camera.config["ff"]["value"]["red"], self.camera.config["ff"]["gain"]["red"]), 1)

        path_to_img = "{}/cam/tmp/{}.jpg".format(self.camera.working_directory, "red")
        imwrite(path_to_img, np.uint8(255*Rr/np.amax(Rr)))

        path_to_img = "{}/cam/tmp/{}.jpg".format(self.camera.working_directory, "nir")
        imwrite(path_to_img, np.uint8(255*Rnir/np.amax(Rnir)))

        # finally calculate ndvi (with some failsafes)
        Rr[Rnir < 0.1] = 0
        Rnir[Rnir < 0.1] = 0
        num = Rnir - Rr
        den = Rnir + Rr
        num[np.logical_and(den < 0.05, den > -0.05)] = 0.0
        den[den < 0.05] = 1.0
        ndvi = np.divide(num, den)
        ndvi[0, 0] = 1.0

        return ndvi


    def ndvi_photo(self):
        """
        Make a photo in the nir and the red spectrum and overlay to obtain ndvi.

        :return: (path to the ndvi image, average ndvi value for >0.25 (iff the #pixels is larger than 2 percent of the total))
        """

        # get the ndvi matrix
        ndvi_matrix = self.ndvi_matrix()

        # catch error
        if ndvi_matrix is None:
            res = dict()
            res["contains_photo"] = False
            res["contains_value"] = False
            res["encountered_error"] = True
            res["timestamp"] = curr_time

            return res

        ndvi_matrix = np.clip(ndvi_matrix, -1.0, 1.0)
        if np.count_nonzero(ndvi_matrix > 0.25) > 0.02*np.size(ndvi_matrix):
            ndvi = np.mean(ndvi_matrix[ndvi_matrix > 0.25])
        else:
            ndvi = 0

        rescaled = np.uint8(np.round(127.5*(ndvi_matrix + 1.0)))

        ndvi_plot = np.copy(ndvi_matrix)
        ndvi_plot[ndvi_plot<0.25] = np.nan

        # write images to file using imageio's imwrite and matplotlibs savefig
        d_print("Writing to file...", 1)
        curr_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

        # set multiprocessing to spawn (so NOT fork)
        try:
            mp.set_start_method('spawn')
        except RuntimeError:
            pass

        # write the matplotlib part in a separate process so no memory leaks
        path_to_img_2 = "{}/cam/img/{}{}_{}.jpg".format(self.camera.working_directory, "ndvi", 2, curr_time)
        p = mp.Process(target=plotter, args=(ndvi_plot, path_to_img_2,))
        try:
            p.start()
            p.join()
        except OSError:
            d_print("Could not start child process, out of memory", 3)

            res = dict()
            res["contains_photo"] = False
            res["contains_value"] = False
            res["encountered_error"] = True
            res["timestamp"] = curr_time

            return res

        path_to_img_1 = "{}/cam/img/{}{}_{}.tif".format(self.camera.working_directory, "ndvi", 1, curr_time)
        imwrite(path_to_img_1, rescaled)

        res = dict()
        res["contains_photo"] = True
        res["contains_value"] = True
        res["encountered_error"] = False
        res["timestamp"] = curr_time
        res["photo_path"] = [path_to_img_1, path_to_img_2]
        res["photo_kind"] = ["raw NDVI", "processed NDVI"]
        res["value"] = [ndvi]
        res["value_kind"] = ["NDVI"]
        res["value_error"] = [0.0]

        return res


    def ndvi(self):
        """
        Make a photo in the nir and the red spectrum and overlay to obtain ndvi.

        :return: average ndvi value
        """

        # get the ndvi matrix
        ndvi_matrix = self.ndvi_matrix()

        # catch error
        if ndvi_matrix is None:
            res = dict()
            res["contains_photo"] = False
            res["contains_value"] = False
            res["encountered_error"] = True
            res["timestamp"] = curr_time

            return res

        ndvi = np.mean(ndvi_matrix[ndvi_matrix > 0.2])

        res = dict()
        res["contains_photo"] = False
        res["contains_value"] = True
        res["encountered_error"] = False
        res["timestamp"] = curr_time
        res["value"] = [ndvi]
        res["value_kind"] = ["NDVI"]
        res["value_error"] = [0.0]

        return res

def plotter(ndvi, path_to_img):
    # set the right colormap
    cmap = plt.get_cmap("nipy_spectral_r")
    Polariks_cmap = truncate_colormap(cmap, 0, 0.6)

    plt.figure(figsize=(14,10))
    plt.imshow(ndvi, cmap=Polariks_cmap)
    plt.colorbar()
    plt.title("NDVI")
    plt.savefig(path_to_img)

    time.sleep(2)
