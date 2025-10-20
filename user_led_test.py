#
# Test the ESP32C6 LED by flashing it.
# The User LED is "active low" so the Signal class is used to logically invert it.
#

import machine
import time

ESP32C6_USER_LED_PIN = 15
DURATION = 2000  # time, in milliseconds, to be on/off
PINS_MAX = 40  # pin range; 0 to PINS_MAX
TOGGLES = 20  # number of times to toggle LED
CYCLES = 3  # number of times to toggle LED

led = machine.Signal(machine.Pin(ESP32C6_USER_LED_PIN, machine.Pin.OUT), invert=True)

# while True:
for n in range(0, CYCLES):
    led.on()
    print(f"ON")
    time.sleep_ms(DURATION)

    led.off()
    print(f"OFF")
    time.sleep_ms(DURATION)
