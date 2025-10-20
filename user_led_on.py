"""
Turn ON the ESP32C6 User LED.
The User LED is "active low" so the Signal class is used to logically invert it.
"""
from machine import Pin,Signal 

ESP32C6_USER_LED_PIN = 15

# led = Pin(ESP32C6_USER_LED_PIN, Pin.OUT)
led = Signal(Pin(ESP32C6_USER_LED_PIN, Pin.OUT), invert=True)

led.on()         # Turn LED on
led.value(True)  # Turn LED on
led.value(1)     # Turn LED on