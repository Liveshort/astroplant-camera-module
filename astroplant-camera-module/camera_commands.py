"""
File that contains an overview of the commands that the camera accepts, grouped by kind.
"""

class CameraCommandType(object):
    """
    Class holding the possible types of commands that can be performed by the camera.
    """

    # regular photo (visible spectrum: ~400-700 nm, color balanced)
    REGULAR_PHOTO = "REGULAR_PHOTO"
    # NDVI photo (NIR vs red spectrum: ~850 nm vs ~630 nm, calibrated to sunlight)
    NDVI_PHOTO = "NDVI_PHOTO"
    # NIR photo (NIR spectrum: ~850 nm)
    NIR_PHOTO = "NIR_PHOTO"
    # leaf mask (should produce a black/white mask that masks out the leaves)
    LEAF_MASK = "LEAF_MASK"

    # visible leaf area from above (does not correct for leaves on top of each other)
    LEAF_AREA_STACKED = "LEAF_AREA_STACKED"
    # plant size along major axis
    PLANT_SIZE_MAJOR = "PLANT_SIZE_MAJOR"
    # plant size along minor axis
    PLANT_SIZE_MINOR = "PLANT_SIZE_MINOR"
    # plant size along minor axis
    PLANT_SIZE_BOUNDING_BOX = "PLANT_SIZE_BOUNDING_BOX"

    # calibrate the camera and the lights
    CALIBRATE = "CALIBRATE"
