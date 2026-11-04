"""
Runs after boot.py (MicroPython executes boot.py then main.py in the same
globals), so it reuses the `display`, `wlan`, `env`, and `connected` that
boot.py already set up.

Keeps the LCD in sync with the live WiFi connection: polls every _POLL_MS and
only touches the display when the connection state actually changes,
reconnecting if the link drops. If boot.py couldn't allocate the display
(display is None — see wifi_connect.boot_connect), retries that here too,
since the heap can look different once WiFi is already up and running.
"""
__license__ = "MIT - https://mit-license.org/"

import sys
import time

from wifi_connect import connect, signal_connected

_POLL_MS = 2000

try:
    while True:
        time.sleep_ms(_POLL_MS)

        if display is None:
            try:
                from display import init_display
                display = init_display()
                from display import show_status
                show_status(display, connected, env.get('SSID'), env.get('IPSK'), mac)
            except (MemoryError, ImportError):
                pass

        is_connected = wlan.isconnected()
        if is_connected != connected:
            connected = is_connected
            if display is not None:
                from display import show_status
                show_status(display, connected, env.get('SSID'), env.get('IPSK'), mac)
            if connected:
                signal_connected()
        if not connected:
            if display is not None:
                from display import show_status
                show_status(display, connected=False, ssid=env.get('SSID'), ipsk=env.get('IPSK'),
                            mac=mac, message="Connecting...")
            connected = connect(wlan, env.get('SSID'), env.get('IPSK'))
            if display is not None:
                from display import show_status
                show_status(display, connected, env.get('SSID'), env.get('IPSK'), mac)
            if connected:
                signal_connected()
except Exception as e:
    with open("crash.log", "w") as f:
        sys.print_exception(e, f)
    raise
