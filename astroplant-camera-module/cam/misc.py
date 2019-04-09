import matplotlib.colors as colors
import numpy as np

# define an empty callback
def empty_callback():
    pass

# define a function that can be passed to routines to control a certain light
def set_light_curry(pi, pin):
    def set_pin_state(state):
        pi.write(pin, state)

    return set_pin_state

def lights_off_curry(channel, light_control):
    def lights_off():
        light_control(channel, 0)

    return lights_off

# ask user to put something white and diffuse in the kit
def place_object_in_kit():
    print("Please remove the plant container and place a white diffuse surface on the bottom plate of the kit and place a small object in the center of the spot of the light and close the kit.")
    print("Type anything to continue.")
    rsp = input("Input: ")

# define a callback to ask the user to remove the object from the kit
def remove_object_from_kit_callback():
    print("Now please remove the small object from the kit and close it up again.")
    print("Type anything to continue.")
    rsp = input("Input: ")

# function used to obtain Polariks ndvi map
def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=100):
    new_cmap = colors.LinearSegmentedColormap.from_list("trunc({n},{a:.2f},{b:.2f})".format(n=cmap.name, a=minval, b=maxval), cmap(np.linspace(minval, maxval, n)))

    return new_cmap
