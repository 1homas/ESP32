## ReadMe

# ESP32

## Boards

This project supports two ESP32-C6 boards:

| Board | Role | Reference |
|---|---|---|
| **Waveshare ESP32-C6-Touch-LCD-1.47** (Amazon: "ESP32-C6 1.47inch Touch Display Development Board") | WiFi status shown on the LCD | `references/waveshare-esp32-c6-touch-lcd-1.47.md` |
| **Seeed Studio XIAO ESP32-C6** (no LCD) | WiFi status signaled by blinking the onboard LED | `references/xiao-esp32c6.md` |

Both run the same `boot.py`/`main.py`/`wifi_connect.py`. The only difference is which optional
files you copy onto the board — `boot.py` detects what's present (`display.py` / `status_led.py`)
and adapts; see "How it works" below. Don't re-derive GPIO pin numbers for either board from
memory or wiki prose — both reference docs above have numbers confirmed on real hardware, and
Waveshare's wiki in particular has been observed to mix in pin numbers from unrelated variants.

## Setup

### Python Virtual Environment

```sh
uv init
uv venv
uv add -r requirements.txt
source .venv/bin/activate
mkdir firmware
touch boot.py main.py
cp .env.example .env
```

### Download MicroPython

[Download MicroPython](https://micropython.org/download/?port=esp32) for your board ( [esp32c6](https://micropython.org/download/?mcu=esp32c6) ) and move it to the `firmware` folder. Same firmware for both boards — they're both ESP32-C6.

> 💡 Use **v1.29.0 or newer**. v1.26.1 has a WiFi driver bug on this board where `wlan.scan()`
> returns zero networks and `wlan.connect()` raises `OSError: Wifi Internal Error`.

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
esptool --chip esp32c6 write-flash 0x0 firmware/ESP32_GENERIC_C6-20260824-v1.29.0.bin
esptool --chip esp32c6 --baud 115200 write-flash 0x0 firmware/ESP32_GENERIC_C6-20260824-v1.29.0.bin
```

### Test

Use `mpremote` to test the ESP32 with MicroPython' REPL:

```sh
# Install `mpremote`
uv add mpremote 

mpremote repl
Connected to MicroPython at /dev/cu.usbmodem1101
Use Ctrl-] or Ctrl-x to exit this shell

>>> print("Hello ESP32C6!")
Hello ESP32C6!
```

## How it works

On boot, `boot.py` connects to WiFi, then `main.py` polls `wlan.isconnected()` and reconnects if
the link drops. How the connection state is *signaled* depends on which optional files are on the
board:

- **Waveshare board**: `display.py` is present, so `main.py` keeps the LCD showing
  CONNECTED/DISCONNECTED + SSID. No touch interaction — it's a pure status display.
- **XIAO board**: `display.py` is absent, so `boot.py`'s `_init_display_retry()` gets an
  `ImportError` and continues with `display = None` — the same `display is None` path already
  used for transient display-allocation failures on the Waveshare board (see below). Instead,
  `status_led.py` is present, so `wifi_connect.signal_connected()` blinks the onboard LED (GPIO15,
  single-color, active-high) 5 times on a successful connect, at boot and on every reconnect.

Both `display.py` and `status_led.py` are optional, presence-detected files: callers try to
import them and treat `ImportError` as "this board doesn't have that," so a board can have
neither, either, or both copied onto it with no code changes.

- `wifi_connect.py` — `.env` loading, the WiFi connect logic (`connect()`), the
  load-env/connect/show-status sequence (`boot_connect()`) called from `boot.py`, and
  `signal_connected()` (LED blink on connect).
- `display.py` — drives the Waveshare board's onboard JD9853 LCD (see
  `references/waveshare-esp32-c6-touch-lcd-1.47.md` for pin mapping) via `show_status()`.
- `status_led.py` — blinks the XIAO board's onboard LED (see `references/xiao-esp32c6.md`).
- `boot.py` — runs once at power-on: allocates the display if present (with retry — see below),
  then delegates to `wifi_connect.boot_connect()` to load `.env`, connect, and signal the result.
- `main.py` — runs after `boot.py` (same globals); polls `wlan.isconnected()` and updates the
  display (if present) on any change, reconnecting if it drops. Also retries display init
  periodically if `boot.py` couldn't allocate it.

## Deploy

1. Edit `.env` with your `SSID` and `IPSK` (and optionally `COUNTRY_CODE`, `HOSTNAME`, `MAC` —
   see `wifi_connect.py`'s docstring for the format). Same `.env` works for either board.

2. **Waveshare board only** — install the LCD driver library:

```sh
mpremote mip install --target lib github:mattytrentini/micropython-jd9853
```

3. Copy files to the board.

   Waveshare (LCD):

   ```sh
   mpremote cp .env :.env
   mpremote cp colors.py :colors.py
   mpremote cp display.py :display.py
   mpremote cp wifi_connect.py :wifi_connect.py
   mpremote cp boot.py :boot.py
   mpremote cp main.py :main.py
   ```

   XIAO (no LCD):

   ```sh
   mpremote cp .env :.env
   mpremote cp wifi_connect.py :wifi_connect.py
   mpremote cp status_led.py :status_led.py
   mpremote cp boot.py :boot.py
   mpremote cp main.py :main.py
   ```

4. Unplug and replug the board.
   - Waveshare: the LCD shows "Connecting...", then CONNECTED or DISCONNECTED + SSID.
   - XIAO: the onboard LED blinks 5 times once connected. To check status directly:
     `mpremote exec "import network; print(network.WLAN(network.STA_IF).ifconfig())"`

   To reprogram the network on either board, just edit `.env` and re-copy it (step 3) — no code
   changes needed.

### A note on the display and memory (Waveshare board)

The display's framebuffer needs one contiguous ~110KB block of RAM, and on this board that
allocation can intermittently fail with `MemoryError` on a real power-on boot due to heap
fragmentation — even though plenty of *total* free memory remains. `boot.py` retries a few times
and, if it still fails, continues without a display (WiFi still comes up fine) rather than
crashing; `main.py` keeps retrying display init in the background. See
`CLAUDE.md`'s "Lessons learned: WiFi + display, v2" section for the full investigation — this is
a real, confirmed constraint of this board/firmware combination, not a bug in this code. This
doesn't apply to the XIAO board, which never allocates a display.

### Debugging without a serial console

`boot.py` and `main.py` each catch their own exceptions and write a traceback to `crash.log` on
the board, since there's no serial output to see otherwise once it's running standalone. Pull it
with:

```sh
mpremote cat :crash.log
```

`boardtool.py` can also grab a live screenshot of the board's current display state without
touching the board's own code (Waveshare board only — the XIAO board has no display to
screenshot):

```sh
uv run python boardtool.py screenshot out.png
```
