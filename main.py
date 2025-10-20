#
# From https://wiki.seeedstudio.com/xiao_esp32c6_micropython/
#

import time
from machine import Pin

LED_PIN = 15

p0 = Pin(LED_PIN, Pin.OUT)    # create output pin on GPIO0

print("HELLO ESP32C6 DEV KIT BOARD")

while True :
    p0.on()                 # set pin to "on" (high) level
    time.sleep(1)
    p0.off()                # set pin to "off" (low) level
    time.sleep(1)