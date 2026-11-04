"""
Runs once at power-on: loads WiFi settings from `.env`, connects to WiFi, and
(on boards with an LCD) shows CONNECTED/DISCONNECTED + SSID.

File layout on the board:
    .env
    boot.py
    display.py     # omit entirely on boards with no LCD, e.g. XIAO ESP32-C6
    status_led.py  # omit entirely on boards with no onboard status LED
    main.py
    wifi_connect.py

.env format: see wifi_connect.py

Copy to the board (Waveshare ESP32-C6-Touch-LCD-1.47):
    mpremote cp .env :.env
    mpremote cp display.py :display.py
    mpremote cp wifi_connect.py :wifi_connect.py
    mpremote cp boot.py :boot.py
    mpremote cp main.py :main.py

Copy to the board (XIAO ESP32-C6, no LCD):
    mpremote cp .env :.env
    mpremote cp wifi_connect.py :wifi_connect.py
    mpremote cp status_led.py :status_led.py
    mpremote cp boot.py :boot.py
    mpremote cp main.py :main.py

Any exception after display init is logged to crash.log (see
wifi_connect.boot_connect), since there's no serial console to see it
otherwise on a standalone boot.
"""
__license__ = "MIT - https://mit-license.org/"

import gc

def _init_display_retry(max_attempts=5):
    """
    The display's ~110KB framebuffer allocation can fail with MemoryError on
    a real power-on boot due to heap fragmentation, even with plenty of
    *total* free memory. Retries with a gc.collect() plus an allocate/free
    churn each time, largest size first, to nudge the allocator into
    merging adjacent free blocks. If every attempt fails, gives up and
    returns None rather than crashing or resetting — WiFi still comes up
    fine without a display (see wifi_connect.boot_connect and main.py,
    which both retry display init periodically once WiFi is up).

    Boards with no LCD (e.g. the XIAO ESP32-C6) simply don't have
    display.py copied onto them, so the ImportError here is the normal,
    permanent "no display on this board" case rather than a transient
    allocation failure.
    """
    try:
        from display import init_display
    except ImportError:
        return None
    for attempt in range(max_attempts):
        gc.collect()
        try:
            return init_display()
        except MemoryError:
            for size in (150000, 100000, 50000, 20000, 5000):
                try:
                    b = bytearray(size)
                    del b
                except MemoryError:
                    pass
            gc.collect()
    return None

display = _init_display_retry()

show_status = None
if display is not None:
    from display import show_status

from wifi_connect import boot_connect

wlan, env, mac, connected = boot_connect(display, show_status)
