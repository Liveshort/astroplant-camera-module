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
    with open("red.field", 'rb') as f:
        red = np.load(f)
    with open("nir.field", 'rb') as f:
        nir = np.load(f)

    plt.figure()
    plt.imshow(red)
    plt.colorbar()
    plt.show(block=False)

    plt.figure()
    plt.plot(get_row(red, 100))
    plt.plot(get_row(red, 275))
    plt.plot(get_row(red, 475))
    plt.plot(get_row(red, 675))
    plt.plot(get_row(red, 850))
    plt.xlabel("pixel [-]")
    plt.ylabel("value [-]")
    plt.legend(["px 100", "px 275", "px 475", "px 675", "px 850"])
    plt.show(block=False)

    plt.figure()
    plt.imshow(nir)
    plt.colorbar()
    plt.show(block=False)

    plt.figure()
    plt.plot(get_row(nir, 100))
    plt.plot(get_row(nir, 275))
    plt.plot(get_row(nir, 475))
    plt.plot(get_row(nir, 675))
    plt.plot(get_row(nir, 850))
    plt.xlabel("pixel [-]")
    plt.ylabel("value [-]")
    plt.legend(["px 100", "px 275", "px 475", "px 675", "px 850"])
    plt.show()
