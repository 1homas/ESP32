import os
import sys
import network

def os_info():
    import os  # lazy load

    print(f"os.uname(): {os.uname()}")
    print(f"os.listdir(): {os.listdir()}")  # os.listdir([dir])
    print(f"os.getcwd(): {os.getcwd()}")


def sys_info():
    """
    Show sys info.
    """
    import sys  # lazy load

    print(f"moduels: {sys.modules}")
    print(f"path: {sys.path}")
    print(f"platform: {sys.platform}")
    print(f"version: {sys.version}")
    print(f"version_info: {sys.version_info}")


def load_dotenv(filename=".env", env: dict = {}):
    """
    Read environment variables from a `.env` file and return a `dict`.
    Args:
        filename (str): the name of the environment data file
        env (dict): an optional dict to append/overwrite
    Returns:
        dict: the dict of environment variables
    """
    # print(f"load_dotenv({filename}, {env})")
    env['env_filename'] = filename
    with open(filename) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                env[key] = value
    return env


# Customize hostname
network.hostname(env.get('HOSTNAME', 'mpy-esp32c6')) # default: 'mpy-esp32c6'

# Customize MAC address
if env.get('MAC', None):
    wlan.config(mac=bytes.fromhex(env.get('MAC')))
    print(f"{wlan.config('mac').hex()=}")
mac = wlan.config('mac')
mac_str = wlan.config('mac').hex()
print(f"WiFi MAC: {wlan.config('mac')} / {len(wlan.config('mac'))} / {wlan.config('mac').hex()}","/",':'.join([f'{i:02x}' for i in mac]))
print(f"mac_str: ",mac_str.encode('utf-8'))  # Return the string encoded to bytes
print(f"back to bytes: ",wlan.config('mac').hex().encode('utf-8'))  # Return the string encoded to bytes

# WLAN info
print(f"{wlan.config('mac')=}")  # Get MAC address, in bytes
print(f"{wlan.config('mac').hex()=}") # Get MAC address, as hex string
print(f"{wlan.config('channel')=}") # must query only one param
