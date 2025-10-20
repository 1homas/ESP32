"""
Find the ESP32C6 User LED by toggling all pins
"""

import machine
import time

DURATION = 100  # time, in milliseconds, to be on/off
PINS_MAX = 40  # pin range; 0 to PINS_MAX
TOGGLES = 20  # number of times to toggle LED

for pin in range(0, PINS_MAX + 1):
    try:
        led = machine.Pin(pin, machine.Pin.OUT)
    except ValueError as e:
        print(f"Pin {pin} is invalid")
        continue

    print(f"Blinking pin {pin} ", end="")  # print '.' for each toggle on same line
    for n in range(0, TOGGLES):
        led.toggle()  # Turn LED off or on
        print(".", end="")
        time.sleep_ms(DURATION)  # Wait between toggles

    print("", end="\n")  # next line

print(f"Done")
