import struct
import unittest
import zlib
from unittest.mock import patch

from boardtool import Board, BoardError, _write_png


def _read_png_pixels(path):
    """
    Minimal PNG decoder for exactly the format _write_png produces:
    8-bit truecolor, no interlace, filter type 0 on every scanline.
    """
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    idat = b""
    width = height = None
    while pos < len(data):
        length = int.from_bytes(data[pos:pos + 4], "big")
        tag = data[pos + 4:pos + 8]
        chunk_data = data[pos + 8:pos + 8 + length]
        if tag == b"IHDR":
            width, height = struct.unpack(">II", chunk_data[:8])
        elif tag == b"IDAT":
            idat += chunk_data
        pos += 8 + length + 4  # length + tag + data + crc

    raw = zlib.decompress(idat)
    stride = 1 + width * 3
    pixels = []
    for y in range(height):
        row = raw[y * stride:(y + 1) * stride]
        assert row[0] == 0  # filter type: none
        row_pixels = []
        for x in range(width):
            o = 1 + x * 3
            row_pixels.append(tuple(row[o:o + 3]))
        pixels.append(row_pixels)
    return pixels


class WritePngTests(unittest.TestCase):
    def test_round_trips_known_colors(self):
        # 2x1 image: pure red (0xF800), pure green (0x07E0), both RGB565 little-endian
        # (the JD9853 driver's framebuffer byte order, confirmed on-device)
        rgb565 = bytes([0x00, 0xF8, 0xE0, 0x07])
        path = "/tmp/test_boardtool_screenshot.png"
        _write_png(path, rgb565, width=2, height=1)

        pixels = _read_png_pixels(path)
        self.assertEqual(pixels[0][0], (255, 0, 0))
        self.assertEqual(pixels[0][1], (0, 255, 0))


class ScreenshotErrorTests(unittest.TestCase):
    def test_screenshot_raises_when_no_live_display_on_board(self):
        board = Board(port="/dev/fake")
        fake_result = type("Result", (), {
            "returncode": 1,
            "stdout": "",
            "stderr": "RuntimeError: no live display object on the board\n",
        })()
        with patch("boardtool.subprocess.run", return_value=fake_result):
            with self.assertRaises(BoardError) as ctx:
                board.screenshot("/tmp/unused.png")
        self.assertIn("no live display object", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
