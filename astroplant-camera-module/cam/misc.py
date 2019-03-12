# define an empty callback
def empty_callback():
    pass

# define a function that can be passed to routines to control a certain light
def set_light_curry(pi, pin):
    def set_pin_state(state):
        pi.write(pin, state)

    return set_pin_state

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
