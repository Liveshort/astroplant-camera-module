import pigpio

light_pins = {
    "flood-white": 2,
    "red": 3,
    "nir": 4,
    "white": 17,
    "yellow": 27,
    "blue": 22,
    "green": 10
}

# set all lights to zero
def set_all_lights_to_zero(pi):
    for key, val in light_pins.items():
        pi.write(val, 0)
