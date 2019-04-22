import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
import matplotlib.pyplot as plt

from PIL import Image

def get_row(array, row):
    return array[row, :]

def get_col(array, col):
    return array[:, col]

if __name__ == "__main__":
    with open("red_rf.field", 'rb') as f:
        red = np.load(f)
    with open("nir_rf.field", 'rb') as f:
        nir = np.load(f)

    # create a list for the calculated reflectances
    R_nir = []
    R_red = []

    # calculate for the lower right corner of the picture
    nir_zeroth = np.mean(nir[950:975, 1175:1200])
    nir_first = np.mean(nir[1070:1095, 1195:1220])
    nir_second = np.mean(nir[1070:1095, 1260:1285])
    nir_black = np.mean(nir[625:650, 1515:1540])

    R_nir.append((nir_first-nir_black)/(nir_zeroth-nir_black))
    R_nir.append((nir_second-nir_black)/(nir_first-nir_black))

    red_zeroth = np.mean(red[950:975, 1175:1200])
    red_first = np.mean(red[1070:1095, 1195:1220])
    red_second = np.mean(red[1070:1095, 1260:1285])
    red_black = np.mean(red[625:650, 1515:1540])

    R_red.append((red_first-red_black)/(red_zeroth-red_black))
    R_red.append((red_second-red_black)/(red_first-red_black))

    # calculate for the upper right corner
    nir_zeroth = np.mean(nir[195:220, 1150:1175])
    nir_first = np.mean(nir[195:220, 1220:1245])
    nir_second = np.mean(nir[130:155, 1220:1245])
    nir_black = np.mean(nir[625:650, 1515:1540])

    R_nir.append((nir_first-nir_black)/(nir_zeroth-nir_black))
    R_nir.append((nir_second-nir_black)/(nir_first-nir_black))

    red_zeroth = np.mean(red[195:220, 1150:1175])
    red_first = np.mean(red[195:220, 1220:1245])
    red_second = np.mean(red[130:155, 1220:1245])
    red_black = np.mean(red[625:650, 1515:1540])

    R_red.append((red_first-red_black)/(red_zeroth-red_black))
    R_red.append((red_second-red_black)/(red_first-red_black))

    # calculate for the upper left corner
    nir_zeroth = np.mean(nir[198:223, 410:435])
    nir_first = np.mean(nir[198:223, 275:300])
    nir_second = np.mean(nir[125:150, 275:300])
    nir_black = np.mean(nir[625:650, 1515:1540])

    R_nir.append((nir_first-nir_black)/(nir_zeroth-nir_black))
    R_nir.append((nir_second-nir_black)/(nir_first-nir_black))

    red_zeroth = np.mean(red[198:223, 410:435])
    red_first = np.mean(red[198:223, 275:300])
    red_second = np.mean(red[125:150, 275:300])
    red_black = np.mean(red[625:650, 1515:1540])

    R_red.append((red_first-red_black)/(red_zeroth-red_black))
    R_red.append((red_second-red_black)/(red_first-red_black))

    # calculate for the lower left corner
    nir_zeroth = np.mean(nir[980:1005, 345:370])
    nir_first = np.mean(nir[1075:1100, 340:365])
    nir_second = np.mean(nir[1075:1100, 250:275])
    nir_black = np.mean(nir[625:650, 1515:1540])

    R_nir.append((nir_first-nir_black)/(nir_zeroth-nir_black))
    R_nir.append((nir_second-nir_black)/(nir_first-nir_black))

    red_zeroth = np.mean(red[980:1005, 345:370])
    red_first = np.mean(red[1075:1100, 340:365])
    red_second = np.mean(red[1075:1100, 250:275])
    red_black = np.mean(red[625:650, 1515:1540])

    R_red.append((red_first-red_black)/(red_zeroth-red_black))
    R_red.append((red_second-red_black)/(red_first-red_black))

    R_nir = np.array(R_nir)
    R_red = np.array(R_red)

    print("red reflectance: {:.2f} \pm {:.2f}".format(np.mean(R_red), np.std(R_red)))
    print("nir reflectance: {:.2f} \pm {:.2f}".format(np.mean(R_nir), np.std(R_nir)))
