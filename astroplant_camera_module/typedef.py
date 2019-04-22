class CC(object):
    """
    (C)amera (C)ommand: Class holding the possible types of commands that can be performed by the camera.
    """

    # regular photo (visible spectrum: ~400-700 nm, color balanced)
    REGULAR_PHOTO = "REGULAR_PHOTO"
    # NDVI photo (NIR vs red spectrum: ~850 nm vs ~630 nm)
    NDVI_PHOTO = "NDVI_PHOTO"
    # NIR photo (NIR spectrum: ~850 nm)
    NIR_PHOTO = "NIR_PHOTO"
    # leaf mask (should produce a black/white mask that masks out the leaves)
    LEAF_MASK = "LEAF_MASK"

    # averaged ndvi value of the plant (all material with ndvi > 0.2)
    NDVI = "NDVI"

    # calibrate the camera and the lights
    CALIBRATE = "CALIBRATE"
    # update camera settings if camera needs this (for example, redetermine gains etc)
    UPDATE = "UPDATE"


class LC(object):
    """
    (L)ight (C)hannel: Class holding the possible channels that can be used to light the kit
    """

    WHITE = "white"
    RED = "red"
    NIR = "nir"
