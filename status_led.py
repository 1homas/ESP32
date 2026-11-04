"""
Blinks the onboard single-color LED a fixed number of times — used to signal
"WiFi connected" on boards with no display (e.g. the XIAO ESP32-C6, GPIO15).

Optional, like display.py: boards without this LED simply don't get this
file copied, and callers treat the resulting ImportError the same way
boot.py already treats a missing display.py.
"""
__license__ = "MIT - https://mit-license.org/"

from machine import Pin
import time

_PIN = 15
_BLINK_MS = 150


def blink(times: int = 5) -> None:
    """
    Args:
        times (int): number of on/off blinks
    """
    led = Pin(_PIN, Pin.OUT)
    led.value(0)
    for _ in range(times):
        led.value(1)
        time.sleep_ms(_BLINK_MS)
        led.value(0)
        time.sleep_ms(_BLINK_MS)
