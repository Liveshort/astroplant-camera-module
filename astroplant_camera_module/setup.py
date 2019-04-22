import os

def check_directories():
    wd = os.getcwd()
    camdir = wd + "/cam"

    if not os.path.isdir(camdir):
        os.mkdir(camdir)

    if not os.path.isdir(camdir + "/cfg"):
        os.mkdir(camdir + "/cfg")

    if not os.path.isdir(camdir + "/img"):
        os.mkdir(camdir + "/img")

    if not os.path.isdir(camdir + "/tst"):
        os.mkdir(camdir + "/tst")

    if not os.path.isdir(camdir + "/res"):
        os.mkdir(camdir + "/res")

    if not os.path.isdir(camdir + "/tmp"):
        os.mkdir(camdir + "/tmp")
