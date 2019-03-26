import time
import pickle
import os
import pprint as pp

import numpy as np
import matplotlib.pyplot as plt

if __name__ == "__main__":
    # total number of measurements
    N = 43

    # give coordinates [x1 y1 x2 y2] of a dark, gray and white block
    blk_c = [691, 376, 713, 401]
    gry_c = [724, 378, 747, 401]
    wht_c = [714, 668, 745, 715]

    # open the settings saved by the capture
    with open('gains.pkl', 'rb') as f:
        actual_gains = pickle.load(f)

    with open('settings.pkl', 'rb') as f:
        settings = pickle.load(f)

    # set up the different plots
    exposure = [0, 13]
    analog_gain = [13, 28]
    digital_gain = [28, N]

    x_exposure = []
    x_analog_gain = []
    x_digital_gain = []
    for i in range(exposure[0], exposure[1]):
        x_exposure.append(settings[i][1])
    for i in range(analog_gain[0], analog_gain[1]):
        x_analog_gain.append(settings[i][2])
    for i in range(digital_gain[0], digital_gain[1]):
        x_digital_gain.append(settings[i][3])
    x_exposure = np.array(x_exposure)
    x_analog_gain = np.array(x_analog_gain)
    x_digital_gain = np.array(x_digital_gain)

    pp.pprint(actual_gains)
    pp.pprint(settings)

    # extract the usefull information from the images
    rgb = []
    black = []
    gray = []
    white = []

    r_blk_avg = []
    r_gry_avg = []
    r_wht_avg = []
    g_blk_avg = []
    g_gry_avg = []
    g_wht_avg = []
    b_blk_avg = []
    b_gry_avg = []
    b_wht_avg = []
    r_blk_std = []
    r_gry_std = []
    r_wht_std = []
    g_blk_std = []
    g_gry_std = []
    g_wht_std = []
    b_blk_std = []
    b_gry_std = []
    b_wht_std = []

    for i in range(N):
        rgb.append(np.load("{}/dat/{}.np".format(os.getcwd(), i)))

        black.append(rgb[i][blk_c[1]:blk_c[3], blk_c[0]:blk_c[2], :])
        gray.append(rgb[i][gry_c[1]:gry_c[3], gry_c[0]:gry_c[2], :])
        white.append(rgb[i][wht_c[1]:wht_c[3], wht_c[0]:wht_c[2], :])

        avg = np.mean(black[i], (0, 1))
        r_blk_avg.append(avg[0])
        g_blk_avg.append(avg[1])
        b_blk_avg.append(avg[2])
        avg = np.mean(gray[i], (0, 1))
        r_gry_avg.append(avg[0])
        g_gry_avg.append(avg[1])
        b_gry_avg.append(avg[2])
        avg = np.mean(white[i], (0, 1))
        r_wht_avg.append(avg[0])
        g_wht_avg.append(avg[1])
        b_wht_avg.append(avg[2])

        std = np.std(black[i], (0, 1))
        r_blk_std.append(std[0])
        g_blk_std.append(std[1])
        b_blk_std.append(std[2])
        std = np.std(gray[i], (0, 1))
        r_gry_std.append(std[0])
        g_gry_std.append(std[1])
        b_gry_std.append(std[2])
        std = np.std(white[i], (0, 1))
        r_wht_std.append(std[0])
        g_wht_std.append(std[1])
        b_wht_std.append(std[2])

    # plot the figure for exposure times
    plt.figure(figsize=(10,8))
    plt.plot(x_exposure, r_blk_avg[exposure[0]:exposure[1]], linestyle='None', marker='p', markersize=8, color='r')
    plt.plot(x_exposure, r_gry_avg[exposure[0]:exposure[1]], linestyle='None', marker='v', markersize=8, color='r')
    plt.plot(x_exposure, r_wht_avg[exposure[0]:exposure[1]], linestyle='None', marker='*', markersize=8, color='r')
    plt.plot(x_exposure, g_blk_avg[exposure[0]:exposure[1]], linestyle='None', marker='p', markersize=8, color='g')
    plt.plot(x_exposure, g_gry_avg[exposure[0]:exposure[1]], linestyle='None', marker='v', markersize=8, color='g')
    plt.plot(x_exposure, g_wht_avg[exposure[0]:exposure[1]], linestyle='None', marker='*', markersize=8, color='g')
    plt.plot(x_exposure, b_blk_avg[exposure[0]:exposure[1]], linestyle='None', marker='p', markersize=8, color='b')
    plt.plot(x_exposure, b_gry_avg[exposure[0]:exposure[1]], linestyle='None', marker='v', markersize=8, color='b')
    plt.plot(x_exposure, b_wht_avg[exposure[0]:exposure[1]], linestyle='None', marker='*', markersize=8, color='b')
    plt.xlabel("Exposure time [$\mu$s]")
    plt.ylabel("Pixel value [-]")
    plt.legend(["Dark block RGB", "Gray block RGB", "Bright block RGB"])
    plt.show(block=False)

    # plot the figure for the analog gains
    plt.figure(figsize=(10,8))
    plt.plot(x_analog_gain, r_blk_avg[analog_gain[0]:analog_gain[1]], linestyle='None', marker='p', markersize=8, color='r')
    plt.plot(x_analog_gain, r_gry_avg[analog_gain[0]:analog_gain[1]], linestyle='None', marker='v', markersize=8, color='r')
    plt.plot(x_analog_gain, r_wht_avg[analog_gain[0]:analog_gain[1]], linestyle='None', marker='*', markersize=8, color='r')
    plt.plot(x_analog_gain, g_blk_avg[analog_gain[0]:analog_gain[1]], linestyle='None', marker='p', markersize=8, color='g')
    plt.plot(x_analog_gain, g_gry_avg[analog_gain[0]:analog_gain[1]], linestyle='None', marker='v', markersize=8, color='g')
    plt.plot(x_analog_gain, g_wht_avg[analog_gain[0]:analog_gain[1]], linestyle='None', marker='*', markersize=8, color='g')
    plt.plot(x_analog_gain, b_blk_avg[analog_gain[0]:analog_gain[1]], linestyle='None', marker='p', markersize=8, color='b')
    plt.plot(x_analog_gain, b_gry_avg[analog_gain[0]:analog_gain[1]], linestyle='None', marker='v', markersize=8, color='b')
    plt.plot(x_analog_gain, b_wht_avg[analog_gain[0]:analog_gain[1]], linestyle='None', marker='*', markersize=8, color='b')
    plt.xlabel("Analog Gain [-]")
    plt.ylabel("Pixel value [-]")
    plt.legend(["Dark block RGB", "Gray block RGB", "Bright block RGB"])
    plt.show(block=False)

    # plot the figure for the digital gains
    plt.figure(figsize=(10,8))
    plt.plot(x_digital_gain, r_blk_avg[digital_gain[0]:digital_gain[1]], linestyle='None', marker='p', markersize=8, color='r')
    plt.plot(x_digital_gain, r_gry_avg[digital_gain[0]:digital_gain[1]], linestyle='None', marker='v', markersize=8, color='r')
    plt.plot(x_digital_gain, r_wht_avg[digital_gain[0]:digital_gain[1]], linestyle='None', marker='*', markersize=8, color='r')
    plt.plot(x_digital_gain, g_blk_avg[digital_gain[0]:digital_gain[1]], linestyle='None', marker='p', markersize=8, color='g')
    plt.plot(x_digital_gain, g_gry_avg[digital_gain[0]:digital_gain[1]], linestyle='None', marker='v', markersize=8, color='g')
    plt.plot(x_digital_gain, g_wht_avg[digital_gain[0]:digital_gain[1]], linestyle='None', marker='*', markersize=8, color='g')
    plt.plot(x_digital_gain, b_blk_avg[digital_gain[0]:digital_gain[1]], linestyle='None', marker='p', markersize=8, color='b')
    plt.plot(x_digital_gain, b_gry_avg[digital_gain[0]:digital_gain[1]], linestyle='None', marker='v', markersize=8, color='b')
    plt.plot(x_digital_gain, b_wht_avg[digital_gain[0]:digital_gain[1]], linestyle='None', marker='*', markersize=8, color='b')
    plt.xlabel("Digital Gain [-]")
    plt.ylabel("Pixel value [-]")
    plt.legend(["Dark block RGB", "Gray block RGB", "Bright block RGB"])
    plt.show(block=False)

    plt.figure()
    plt.imshow(rgb[5])
    plt.show()
