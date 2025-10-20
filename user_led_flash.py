"""
Flash the ESP32C6 LED

Usage:
  mpremote run user_led_flash.py

"""

import machine
import time

ESP32C6_USER_LED_PIN = 15
DURATION = 100  # time, in milliseconds, to be on/off

led = machine.Pin(ESP32C6_USER_LED_PIN, machine.Pin.OUT)

while True:
    led.toggle()  # Turn LED off or on
    time.sleep_ms(DURATION)  # Wait for 1 second
