"""
Named RGB565 colors and conversion helper, shared across display.py and
anything else drawing to the JD9853 framebuffer.
"""
__license__ = "MIT - https://mit-license.org/"


def rgb565(r: int, g: int, b: int) -> int:
    """
    Args:
        r, g, b (int): 8-bit color components (0-255)
    Returns:
        int: packed RGB565 value
    """
    return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)


BLACK = 0x0000
WHITE = 0xFFFF
RED = 0xF800
GREEN = 0x07E0
BLUE = 0x001F
DARK_GREEN = 0x0320
DARK_RED = 0x8000
YELLOW = rgb565(255, 255, 0)
ORANGE = rgb565(255, 165, 0)
CYAN = rgb565(0, 255, 255)
MAGENTA = rgb565(255, 0, 255)
GRAY = rgb565(128, 128, 128)
