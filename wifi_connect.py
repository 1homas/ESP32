"""
Copy to `boot.py` on the ESP32 for automatic WiFi connection upon boot.
It relies on your secret WiFi settings in a `.env` file:
  SSID=your_ssid_name
  IPSK=pre_shared_key

    .
    ├── .env
    ├── boot.py
    └── main.py

  mpremote cp .env :.env
  mpremote cp wifi_connect.py :boot.py

"""

import network
import time
import machine
import ntptime
from machine import Pin,Signal

ESP32C6_USER_LED_PIN = 15
MAX_RETRIES = 30  # Connect retries
TIMEOUT = 500  # WLAN connect timeout, in milliseconds

def blink(cycles:int=20, hold:int=1000):
    """
    Blink the ESP32C6_USER_LED_PIN.
    Args:
        cycles (int): number of cycles
        hold (int): time, in milliseconds, to hold LED on and off
    """
    led = Signal(Pin(ESP32C6_USER_LED_PIN, Pin.OUT), invert=True)
    for n in range(0,cycles) :
        led.on()
        time.sleep_ms(hold)
        led.off()
        time.sleep_ms(hold)

def load_dotenv(filename=".env", env: dict = {}):
    """
    Read environment variables from a `.env` file and return a `dict`.
    Args:
        filename (str): the name of the environment data file
        env (dict): an optional dict to append/overwrite
    Returns:
        dict: the dict of environment variables
    """
    env['env_filename'] = filename
    with open(filename) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                env[key] = value
    return env


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


if __name__ == "__main__":

    env = load_dotenv()
    print(f"Loaded .env: {env.keys()}")

    if env.get('COUNTRY_CODE', None):
        network.country(env.get('COUNTRY_CODE'))
        print(f"{network.country()=}")  # default: 'XX'
    if env.get('HOST', None):
        network.hostname(env.get('HOST'))
        print(f"{network.hostname()=}")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)  # Activate the interface
    print(f"WiFi MAC: {wlan.config('mac')} | {wlan.config('mac').hex()}","|",':'.join([f'{i:02x}' for i in wlan.config('mac')]))

    if wifi_connect(wlan, ssid=env.get('SSID'), ipsk=env.get('IPSK')):
        print("ESP32-C6 is successfully connected to the internet.")

        # Synchronize the clock with an NTP server
        try:
            ntptime.host = 'pool.ntp.org' # default
            ntptime.settime()
            print('Clock synchronized successfully.')

            rtc = machine.RTC()
            yyyy, mm, dd, wd, hh, mm, ss, ms = rtc.datetime()
            print(f'Current time: {yyyy}-{mm:02d}-{dd:02d} {hh:02d}:{mm:02d}:{ss:02d}:{ms:03d} UTC')

        except OSError:
            print('Failed to synchronize the clock.')

        blink(20,100)  # Fast blink LED if OK


    else:
        # Optionally, put the device into a low-power state or retry machine.reset()
        print("Could not establish WiFi connection. Please check credentials and try again.")
        blink(20,100)  # Slow blink LED if not OK


