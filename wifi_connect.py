"""
Connects ESP32C6 to WiFi using network settings in a `.env` file.

File layout:

    .
    ├── .env
    ├── boot.py
    └── main.py

Loads WiFi settings from a `.env` file:

    # Network Settings
    COUNTRY_CODE=US
    HOSTNAME=esp32-c6-micropython
    # WLAN Settings
    MAC=01:23:45:67:89:ab
    SSID=your_ssid_name
    IPSK=pre_shared_key

Copy to `boot.py` on the ESP32 for automatic WiFi connection upon boot.
  mpremote cp .env :.env
  mpremote cp wifi_connect.py :boot.py

"""
__license__ = "MIT - https://mit-license.org/"

import machine
import network
import ntptime
import time

ESP32C6_USER_LED_PIN = 15
MAX_RETRIES = 30  # Connect retries
TIMEOUT = 500  # WLAN connect timeout, in milliseconds


def blink(cycles: int = 20, hold: int = 1000):
    """
    Blink the ESP32C6_USER_LED_PIN.
    Args:
        cycles (int): number of cycles
        hold (int): time, in milliseconds, to hold LED on and off
    """
    led = machine.Signal(machine.Pin(ESP32C6_USER_LED_PIN, machine.Pin.OUT), invert=True)
    for n in range(0, cycles):
        led.on()
        print(f"🟡", end='')
        time.sleep_ms(hold)
        led.off()
        print(f"⚫", end='')
        time.sleep_ms(hold)
    print() # newline

def load_dotenv(filename: str = ".env", env: dict = {}):
    """
    Read environment variables from a `.env` file and return a `dict`.
    Args:
        filename (str): the name of the environment data file
        env (dict): an optional dict to append/overwrite
    Returns:
        dict: the dict of environment variables
    """
    env['env_filename'] = filename
    try:
        with open(filename) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    env[key] = value
        print(f"Loaded .env: {list(env.keys())}")
    except OSError:
        print(f"No env file")
    return env


def wlan_mac(wlan, mac: str = None):
    """
    Args:
        wlan (network.WLAN) : the WLAN interface
        mac (str) : MAC address, may be delimited or not
    Returns:
        wlan: the WLAN interface
    """
    if not isinstance(mac, str):
        raise TypeError(f"mac is not a string")
    # normalize
    mac = ''.join(c for c in mac if c in '0123456789abcdefABCDEF').upper()
    if len(mac) != 12:
        raise ValueError(f"Invalid MAC: {mac}")
    print(f"MAC {mac} in bytes {bytes.fromhex(mac)}")
    wlan.config(mac=bytes.fromhex(mac))  # set new MAC address in bytes
    return wlan


def mac_format(mac: str = None, separator: str = ':', digits: int = 2):
    """
    Formats a MAC address with the specified separator
    Args:
        mac (str) : MAC address, may be delimited or not
        separator (str) : the separator (default: ':'), must be one of ['',':','.','-']
        digits : number of hex digits between separators, 2 (default) or 4
    Returns:
        wlan: the WLAN interface
    """
    if not isinstance(mac, str):
        raise ValueError(f"Invalid MAC string: {mac}")
    if not isinstance(digits, int) and digits not in [2, 4]:
        raise ValueError(f"Invalid number of digits: {digits}")
    if separator != '' and separator not in ':.-':
        raise ValueError(f"Separator must be '' or [:.-]: {separator}")
    # normalize
    mac = ''.join(c for c in mac if c in '0123456789abcdefABCDEF').upper()
    if len(mac) != 12:
        raise ValueError(f"Invalid MAC: {mac}")
    return separator.join(f"{mac[i:i+digits]}" for i in range(0, 12, digits))


def wlan_connect(wlan: network.WLAN = None, ssid: str = None, ipsk: str = None):
    """
    Connects the ESP32-C6 to a WiFi network.
    Args:
        wlan (network.WLAN) : the WLAN interface
        ssid (str) : security set identifier
        ipsk (str) : [identity] pre-shared key
    Returns:
        bool: True for success, False otherwise.
    """
    if wlan is None:
        wlan = network.WLAN(network.wlan)  # default: station interface
    wlan.active(True)  # Activate the interface

    if not wlan.isconnected():
        print(f"Connecting to {ssid} WiFi network ...")
        wlan.connect(ssid, ipsk)  # Connect to the network using SSID and PSK

        # Wait for MAX_RETRIES * TIMEOUT to connect
        attempts = 0
        while not wlan.isconnected() and attempts < MAX_RETRIES:
            print(f".", end="")
            time.sleep_ms(TIMEOUT)
            attempts += 1

        if wlan.isconnected():
            print(
                f"WiFi {wlan.config('mac').hex()} connected @ {wlan.ifconfig()}")
            return True
        else:
            print(f"WiFi Failed to connect: {NETWORK_STATUS[wlan.status()]}")
            return False
    else:
        print(
            f"WiFi {wlan.config('mac').hex()} already connected @ {wlan.ifconfig()}")
        return True


def wifi_connect(wlan: network.WLAN = None, ssid: str = None, ipsk: str = None):
    """
    Connects the ESP32-C6 to a WiFi network.
    Args:
        wlan (network.WLAN) : the WLAN interface
        ssid (str) : security set identifier
        ipsk (str) : [identity] pre-shared key
    Returns:
        bool: True for success, False otherwise.
    """
    if wlan is None:
        wlan = network.WLAN(network.STA_IF)  # default: station interface
    wlan.active(True)  # Activate the interface

    if not wlan.isconnected():
        print(f"Connecting to WiFi network: {ssid}...")
        wlan.connect(ssid, ipsk)  # Connect to the network using SSID and PSK

        # Wait for MAX_RETRIES * TIMEOUT to connect
        attempts = 0
        while not wlan.isconnected() and attempts < MAX_RETRIES:
            print(f".", end="")
            time.sleep_ms(TIMEOUT)
            attempts += 1

        if wlan.isconnected():
            print(f"WiFi {wlan.config('mac').hex()} connected @ {wlan.ifconfig()}")
            return True
        else:
            print(f"WiFi Failed to connect: {NETWORK_STATUS[wlan.status()]}")
            return False
    else:
        print(f"WiFi {wlan.config('mac').hex()} already connected @ {wlan.ifconfig()}")
        return True


def ntp_sync():
    """
    Synchronize the RTC clock with an NTP server.
    """
    try:
        ntptime.host = 'pool.ntp.org'  # default
        ntptime.settime()
        print('Clock synced')
        rtc = machine.RTC()
        yyyy, mm, dd, wd, hh, mm, ss, ms = rtc.datetime()
        print(
            f'Current time: {yyyy}-{mm:02d}-{dd:02d} {hh:02d}:{mm:02d}:{ss:02d}.{ms:03d} UTC')
    except OSError:
        print('Clock sync Failed')


if __name__ == "__main__":

    env = load_dotenv()

    # Network Settings
    if env.get('COUNTRY_CODE', None):
        network.country(env.get('COUNTRY_CODE'))
        print(f"{network.country()=}")  # default: 'XX'
    if env.get('HOSTNAME', None):
        network.hostname(env.get('HOSTNAME'))
        print(f"{network.hostname()=}")

    # MAC Settings
    wlan = network.WLAN(network.STA_IF)
    if env.get('MAC', None):
        wlan_mac(wlan, env.get('MAC'))
        print(f"MAC is {mac_format(wlan.config('mac').hex())}")
    wlan.active(True)  # Activate the interface
    if wlan_connect(wlan, ssid=env.get('SSID'), ipsk=env.get('IPSK')):
        print("✅ ESP32-C6 is successfully connected to the internet.")
        ntp_sync()
        blink(20, 100)  # Fast blink LED if OK
    else:
        # Optionally, put the device into a low-power state or retry machine.reset()
        print("❌ Could not establish WiFi connection. Please check credentials and try again.")
        blink(20, 500)  # Slow blink LED if not OK

