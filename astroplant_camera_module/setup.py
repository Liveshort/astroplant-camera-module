import os

def check_directories(root_directory):
    """
    Sets up the necessary directories for the camera to work. Everything is created relative to the root directory supplied by the user.
    """

    camdir = root_directory + "/cam"

    if not os.path.isdir(camdir):
        os.mkdir(camdir)

    if not os.path.isdir(camdir + "/cfg"):
        os.mkdir(camdir + "/cfg")

    if not os.path.isdir(camdir + "/img"):
        os.mkdir(camdir + "/img")

    if not os.path.isdir(camdir + "/res"):
        os.mkdir(camdir + "/res")

    if not os.path.isdir(camdir + "/tmp"):
        os.mkdir(camdir + "/tmp")
