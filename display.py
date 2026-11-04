"""
Drives the onboard JD9853 LCD on the Waveshare ESP32-C6-Touch-LCD-1.47.

Pin mapping: see references/waveshare-esp32-c6-touch-lcd-1.47.md
"""
__license__ = "MIT - https://mit-license.org/"

import framebuf
from machine import Pin, SPI

from jd9853 import JD9853

from colors import DARK_GREEN, DARK_RED, WHITE

_FONT_PX = 8  # built-in framebuf font is 8x8


def init_display(rotation=270):
    """
    Returns:
        JD9853: the initialized display object
    """
    Pin(4, Pin.OUT, value=1)  # SD_CS: keep SD card deselected (shares the SPI bus)
    spi = SPI(1, baudrate=40_000_000, polarity=0, phase=0,
              bits=8, firstbit=SPI.MSB, sck=Pin(1), mosi=Pin(2), miso=Pin(3))
    display = JD9853(spi,
                      cs=Pin(14, Pin.OUT, value=1),
                      dc=Pin(15, Pin.OUT, value=0),
                      reset=Pin(22, Pin.OUT, value=1),
                      rotation=rotation)
    Pin(23, Pin.OUT, value=1)  # backlight on
    return display


def draw_text(display, text: str, x: int, y: int, color: int, scale: int = 1):
    """
    Draw text using the built-in 8x8 font, scaled up by pixel-doubling.
    Args:
        display: a framebuf.FrameBuffer-compatible display
        text (str): text to draw
        x, y (int): top-left position
        color (int): RGB565 color
        scale (int): integer scale factor (1 = native 8x8 font)
    """
    text = str(text)
    if scale == 1:
        display.text(text, x, y, color)
        return
    glyph_buf = bytearray(_FONT_PX)
    glyph = framebuf.FrameBuffer(glyph_buf, _FONT_PX, _FONT_PX, framebuf.MONO_VLSB)
    for i, ch in enumerate(text):
        for b in range(len(glyph_buf)):
            glyph_buf[b] = 0
        glyph.text(ch, 0, 0, 1)
        cx = x + i * _FONT_PX * scale
        for gy in range(_FONT_PX):
            for gx in range(_FONT_PX):
                if glyph.pixel(gx, gy):
                    display.fill_rect(cx + gx * scale, y + gy * scale, scale, scale, color)


def show_status(display, connected: bool, ssid: str, ipsk: str, mac: str, message: str = None):
    """
    Render the static network details (MAC, SSID, IPSK) at the top of the LCD
    and the live connection status at the bottom.
    Args:
        display (JD9853): the display object from init_display()
        connected (bool): WiFi connection status
        ssid (str): network SSID
        ipsk (str): [identity] pre-shared key
        mac (str): formatted MAC address (see wifi_connect.mac_format), e.g. for
            registering this device's identity on an Identity-PSK network
        message (str): status line to show instead of CONNECTED/DISCONNECTED,
            e.g. "Connecting..."
    """
    display.fill(DARK_GREEN if connected else DARK_RED)
    y = 8
    for label, value in (("MAC:", mac), ("SSID:", ssid or "(none)"), ("IPSK:", ipsk or "(none)")):
        draw_text(display, label, 8, y, WHITE, 1)
        y += 12
        draw_text(display, value, 8, y, WHITE, 2)
        y += 26

    status_text = message or ("CONNECTED" if connected else "DISCONNECTED")
    draw_text(display, status_text, 8, display.height - 28, WHITE, 2)
    display.show()
