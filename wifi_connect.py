"""
WiFi connection helpers and `.env` loading, shared by `boot.py` and `main.py`.

`load_dotenv()` and `mac_format()` are pure (no hardware import) and covered by
`test_wifi_connect.py` on desktop. `wlan_mac()` and `connect()` touch a live
`network.WLAN` object and are only validated on-device.

.env format:
    COUNTRY_CODE=US
    HOSTNAME=esp32-c6-micropython
    MAC=01:23:45:67:89:ab
    SSID=your_ssid_name
    IPSK=pre_shared_key
"""
__license__ = "MIT - https://mit-license.org/"

import time

ATTEMPT_TIMEOUT_MS = 15_000  # how long to poll before giving up on one attempt
POLL_MS = 500  # how often to check isconnected()


def load_dotenv(filename: str = ".env") -> dict:
    """
    Args:
        filename (str): the name of the environment data file
    Returns:
        dict: parsed KEY=VALUE pairs from the file (empty if the file is missing)
    """
    env = {}
    try:
        with open(filename) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env[key] = value
    except OSError:
        print(f"No {filename} found")
    return env


def mac_format(mac: str, separator: str = ':') -> str:
    """
    Args:
        mac (str): MAC address, delimited or not
        separator (str): separator to insert between byte pairs
    Returns:
        str: the normalized, re-delimited MAC address
    """
    mac = ''.join(c for c in mac if c in '0123456789abcdefABCDEF').upper()
    if len(mac) != 12:
        raise ValueError(f"Invalid MAC: {mac}")
    return separator.join(mac[i:i + 2] for i in range(0, 12, 2))


def wlan_mac(wlan, mac: str):
    """
    Args:
        wlan (network.WLAN): the WLAN interface
        mac (str): MAC address, delimited or not
    Returns:
        network.WLAN: the same interface, for chaining
    """
    wlan.config(mac=bytes.fromhex(mac_format(mac, separator='')))
    return wlan


def signal_connected() -> None:
    """
    Blinks the onboard status LED (see status_led.py) to signal a successful
    WiFi connection. Boards with no such LED simply don't have
    status_led.py copied onto them, so the ImportError here is the normal
    "no status LED on this board" case.
    """
    try:
        from status_led import blink
    except ImportError:
        return
    blink()


def boot_connect(display, show_status):
    """
    Loads `.env`, brings up WiFi, connects, and logs any exception to
    crash.log — called from `boot.py` only after `init_display()` has
    already run, and kept in this separate module rather than written
    inline in boot.py itself. Confirmed on-device: MicroPython compiles a
    whole .py file's bytecode upfront before executing any of it, so this
    logic (plus the `sys` import and try/except needed to log crashes)
    written out inline in boot.py still costs heap *before*
    `init_display()` runs there, and reliably blows its ~110KB framebuffer
    allocation on a real power-on boot. Keeping it in this module, imported
    by boot.py only after init_display() succeeds, means that cost lands
    after the display is already allocated.
    Args:
        display: the display object from init_display(), or None if display
            init failed (e.g. MemoryError) — WiFi still comes up either way
        show_status: display.show_status, passed in rather than imported
            here to avoid importing display.py a second time; ignored if
            display is None
    Returns:
        tuple: (wlan, env, mac, connected)
    """
    import sys

    try:
        import network

        env = load_dotenv()
        if env.get('COUNTRY_CODE'):
            network.country(env['COUNTRY_CODE'])
        if env.get('HOSTNAME'):
            network.hostname(env['HOSTNAME'])

        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if env.get('MAC'):
            wlan_mac(wlan, env['MAC'])
        mac = mac_format(wlan.config('mac').hex())

        if display is not None:
            show_status(display, connected=False, ssid=env.get('SSID'), ipsk=env.get('IPSK'),
                        mac=mac, message="Connecting...")
        connected = connect(wlan, env.get('SSID'), env.get('IPSK'))
        if display is not None:
            show_status(display, connected, env.get('SSID'), env.get('IPSK'), mac)
        if connected:
            signal_connected()
        return wlan, env, mac, connected
    except Exception as e:
        with open("crash.log", "w") as f:
            sys.print_exception(e, f)
        raise


def connect(wlan, ssid: str, ipsk: str) -> bool:
    """
    Connects (or confirms connection) to a WiFi network. Retries once through
    the "Wifi Internal Error" OSError that wlan.connect() can raise when the
    driver's internal state hasn't settled yet right after activation.
    Args:
        wlan (network.WLAN): the WLAN interface, already wlan.active(True)
        ssid (str): network SSID
        ipsk (str): [identity] pre-shared key
    Returns:
        bool: True if connected, False if every attempt failed
    """
    if wlan.isconnected():
        return True

    for attempt in range(2):
        try:
            wlan.connect(ssid, ipsk)
        except OSError as e:
            print(f"wlan.connect() raised {e}, resetting WiFi interface")
            wlan.active(False)
            time.sleep_ms(200)
            wlan.active(True)
            continue

        attempt_start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), attempt_start) < ATTEMPT_TIMEOUT_MS:
            if wlan.isconnected():
                return True
            time.sleep_ms(POLL_MS)

        print(f"WiFi failed to connect, status={wlan.status()}")
        wlan.active(False)
        time.sleep_ms(200)
        wlan.active(True)

    return False
