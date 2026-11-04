import unittest

import colors
from colors import rgb565


class NamedColorTests(unittest.TestCase):
    def test_named_colors_match_rgb565_construction(self):
        self.assertEqual(colors.YELLOW, rgb565(255, 255, 0))
        self.assertEqual(colors.ORANGE, rgb565(255, 165, 0))
        self.assertEqual(colors.CYAN, rgb565(0, 255, 255))
        self.assertEqual(colors.MAGENTA, rgb565(255, 0, 255))
        self.assertEqual(colors.GRAY, rgb565(128, 128, 128))

    def test_named_colors_are_distinct(self):
        names = ["BLACK", "WHITE", "RED", "GREEN", "BLUE", "DARK_GREEN",
                 "DARK_RED", "YELLOW", "ORANGE", "CYAN", "MAGENTA", "GRAY"]
        values = [getattr(colors, name) for name in names]
        self.assertEqual(len(values), len(set(values)))


class Rgb565Tests(unittest.TestCase):
    def test_pure_red(self):
        self.assertEqual(rgb565(255, 0, 0), 0xF800)

    def test_pure_green(self):
        self.assertEqual(rgb565(0, 255, 0), 0x07E0)

    def test_pure_blue(self):
        self.assertEqual(rgb565(0, 0, 255), 0x001F)

    def test_white(self):
        self.assertEqual(rgb565(255, 255, 255), 0xFFFF)

    def test_black(self):
        self.assertEqual(rgb565(0, 0, 0), 0x0000)


if __name__ == "__main__":
    unittest.main()
