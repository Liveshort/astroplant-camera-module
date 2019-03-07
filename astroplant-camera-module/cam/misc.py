# define an empty callback
def empty_callback():
    pass

# define a function that can be passed to routines to control a certain light
def set_light_curry(pi, pin):
    def set_pin_state(state):
        pi.write(pin, state)

    return set_pin_state
