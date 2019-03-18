import pigpio
import time

SLEEP = 2

if __name__ == "__main__":
    pi = pigpio.pi()

    light_pins = {
        "flood-white": 2,
        "red": 3,
        "nir": 4,
        "spot-white": 17,
        "yellow": 27,
        "blue": 22,
        "green": 10
    }

    time.sleep(5)

    pi.write(light_pins["flood-white"], 1)
    rsp = input("press enter to continue")
    time.sleep(SLEEP)
    pi.write(light_pins["flood-white"], 0)

    pi.write(light_pins["red"], 1)
    rsp = input("press enter to continue")
    time.sleep(SLEEP)
    pi.write(light_pins["red"], 0)

    pi.write(light_pins["nir"], 1)
    time.sleep(SLEEP)
    pi.write(light_pins["nir"], 0)

    pi.write(light_pins["spot-white"], 1)
    time.sleep(SLEEP)
    pi.write(light_pins["spot-white"], 0)

    pi.write(light_pins["yellow"], 1)
    time.sleep(SLEEP)
    pi.write(light_pins["yellow"], 0)

    pi.write(light_pins["blue"], 1)
    time.sleep(SLEEP)
    pi.write(light_pins["blue"], 0)

    pi.write(light_pins["green"], 1)
    time.sleep(SLEEP)
    pi.write(light_pins["green"], 0)
