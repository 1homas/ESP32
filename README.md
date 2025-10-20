## ReadMe

# ESP32

## Setup

### Python Virtual Environment

```sh
uv init
uv venv
uv add -r requirements.txt
source ./venv/bin/activate
mkdir firmware
touch boot.py main.py
cp .env.example .env
```

## Quick Start

### Download MicroPython

[Download MicroPython](https://micropython.org/download/?port=esp32) for your board ( [esp32c6](https://micropython.org/download/?mcu=esp32c6) ) and move it to the `firmware` folder.

### `esptool`

Install `esptool` and use it to erase and flash the board with MicroPython

```sh
uv add esptool
```

### Erase / Factory Reset

```sh
esptool erase-flash                  # 💡 Automatically detect the ESP32 serial port
esptool --port PORTNAME erase_flash  # 💡 Find your ESP serial port: `ls /dev/cu*`
esptool --chip esp32c6 erase_flash
```

### Flash

Write the downloaded MicroPython firmware to the chip:

```sh
esptool --chip esp32c6 write-flash 0x0 firmware/ESP32_GENERIC_C6-20250911-v1.26.1.bin
esptool --chip esp32c6 --baud 115200 write-flash 0x0 firmware/ESP32_GENERIC_C6-20250911-v1.26.1.bin
```

### Test

Use `mpremote` to test the ESP32 with MicroPython' REPL:

```sh
uv add mpremote # Install `mpremote`

mpremote repl
Connected to MicroPython at /dev/cu.usbmodem1101
Use Ctrl-] or Ctrl-x to exit this shell

>>> print("Hello ESP32C6!")
Hello ESP32C6!
```

## `boot.py`

A file named `boot.py` can be copied to the board’s internal filesystem using `mpremote`. If `boot.py` is found then it is executed. You can add code in `boot.py` to perform custom one-off initialisation (for example, to configure the board’s hardware). A common practice is to configure a board’s network connection in `boot.py` so that it’s always available after reset for use with the REPL, mpremote, etc.

## `main.py`

`main.py` is for any Python code that you want to run each time your device starts.
`main.py` doesn’t have to exit, feel free to put an infinite `while True` loop in there.

## `wifi_connect.py`

1. Edit `.env` with your SSID and IPSK values.

2. Plugin your ESP32C6 and verify it works:

```sh
mpremote run wifi_connect.py
```

3. Copy `.env` and `wifi_connect.py` to the ESP32:

> 💡 The `:` prefix for the destination file represents the ESP32 flash filesystem.

```sh
mpremote cp .env :.env
mpremote cp wifi_connect.py :boot.py
```

4. Unplug and replug your ESP32C6 and look for the fast LED flash (success) or slow LED flash (fail).
