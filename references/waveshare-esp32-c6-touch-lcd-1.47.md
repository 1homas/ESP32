# Waveshare ESP32-C6-Touch-LCD-1.47

## Hardware
- Waveshare ESP32-C6-Touch-LCD-1.47
- MCU: ESP32-C6, QFN32 package. `esptool chip-id` over `/dev/cu.usbmodem214101` reports
  `ESP32-C6FH4 (QFN32) (revision v0.2)` — note this conflicts with the Amazon listing text
  ("ESP32-C6FH8", 8MB flash); trust the esptool read (it queries the silicon directly) over
  marketing copy for flash size. Listing copy is frequently wrong/copy-pasted across SKUs.
- Display: 1.47" IPS, **JD9853** driver chip (NOT ST7789 — the non-touch sibling board uses
  ST7789; don't reuse that driver/config here), 172×320 resolution, 262K color, SPI interface.
- Touch controller: AXS5106L, I2C.
- Onboard IMU: QMI8658A, I2C (shares the same I2C bus/pins as touch).
- Onboard TF/microSD card slot, sharing SCLK/MOSI with the LCD (separate CS/MISO).
- USB enumerates as the generic Espressif "USB JTAG/serial debug unit" — gives no board-identifying
  info; board model must come from the physical listing/silkscreen, not USB descriptors.

## Confirmed GPIO Pin Mapping

Source: schematic PDF at
https://files.waveshare.com/wiki/ESP32-C6-Touch-LCD-1.47/ESP32-C6-Touch-LCD-1.47-Schematic.pdf
(extracted directly from the netlist — do not trust the wiki's prose/Arduino-snippet pin tables,
which blended in pin numbers from an unrelated ESP32-S3 variant, e.g. GPIO38-47, impossible on C6).

| Function                  | GPIO  | Notes |
|----------------------------|-------|-------|
| LCD_SCL (SPI clock)        | IO1   | shared with SD_SCLK |
| LCD_SDA (SPI MOSI)         | IO2   | shared with SD_MOSI |
| LCD_CS                     | IO14  | |
| LCD_DC                     | IO15  | |
| LCD_RST                    | IO22  | |
| LCD_BL (backlight)         | IO23  | |
| TP_SCL (touch I2C clock)   | IO19  | shared with IMU_SCL / ESP_SCL |
| TP_SDA (touch I2C data)    | IO18  | shared with IMU_SDA / ESP_SDA |
| TP_RST (touch reset)       | IO20  | |
| TP_INT (touch interrupt)   | IO21  | |
| SD_SCLK                    | IO1   | shared with LCD_SCL |
| SD_MOSI                    | IO2   | shared with LCD_SDA |
| SD_MISO                    | IO3   | |
| SD_CS                      | IO4   | |

## MicroPython Support

No official MicroPython firmware/driver from Waveshare for this board — wiki only documents
Arduino/ESP-IDF demos. JD9853 is a cheap IPS driver with an ST7789-like but not identical command
set; a dedicated or configurable driver is needed rather than assuming ST7789 compatibility.

## Firmware version matters for WiFi

MicroPython **v1.26.1** (`ESP32_GENERIC_C6-20250911-v1.26.1.bin`) has a broken WiFi stack on this
board: `wlan.scan()` returns zero networks (no error) and `wlan.connect()` raises
`OSError: Wifi Internal Error`. Re-flashing **v1.29.0** (`ESP32_GENERIC_C6-20260824-v1.29.0.bin`)
fixed both — scan sees nearby APs and `connect()` succeeds. Always use v1.29.0+ on this board.

Separately: after flashing new firmware or running several scripts back-to-back over the same
`mpremote` session, the device can throw `MemoryError: memory allocation failed, allocating
110080 bytes` when re-initializing the display (110080 bytes = the 320×172 RGB565 framebuffer).
This is heap fragmentation/a stale display object left over from a prior script run (e.g.
`boot.py` already allocated one) — not a real bug. Fix: power-cycle or `mpremote reset` for a
clean heap before testing display init again.

This can also happen on the **very first** boot after a clean reset, with no prior script run at
all: just `import network` — even without activating the interface — reserves enough of the heap
for its internal WiFi buffers to leave no single contiguous 110KB block free, even though total
free heap looks plenty large (confirmed: `gc.mem_free()` was ~165KB post-import vs. ~333KB
pristine). Fix: `init_display()` before `import network` runs at all, not just before
`wlan.active(True)` — deferring the `import` itself, not only its usage, matters.

## Lesson learned (expensive one)

An entire debugging session was spent driving GPIO22 (actually **LCD_RST** on this board) expecting
it to be the backlight, because that's what GPIO22 means on the sibling **non-touch**
ESP32-C6-LCD-1.47 board (see [[waveshare-esp32-c6-lcd-1.47]]). The two boards share a product family
name and look similar in marketing copy, but have **completely different GPIO assignments and LCD
driver chips**. Always pull pin numbers from the schematic PDF matching the *exact* product name,
and extract the netlist text directly rather than trusting a wiki page's prose summary of pins
(which can blend in copy from a related but different board/MCU).
