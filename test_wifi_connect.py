import os
import tempfile
import unittest

import wifi_connect
from wifi_connect import load_dotenv, mac_format


class LoadDotenvTests(unittest.TestCase):
    def test_parses_key_value_pairs(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".env") as f:
            f.write("SSID=my_network\nIPSK=secret123\n")
            path = f.name
        try:
            env = load_dotenv(path)
        finally:
            os.unlink(path)
        self.assertEqual(env, {"SSID": "my_network", "IPSK": "secret123"})

    def test_skips_comments_and_blank_lines(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".env") as f:
            f.write("# comment\n\nSSID=my_network\n")
            path = f.name
        try:
            env = load_dotenv(path)
        finally:
            os.unlink(path)
        self.assertEqual(env, {"SSID": "my_network"})

    def test_missing_file_returns_empty_dict(self):
        self.assertEqual(load_dotenv("/nonexistent/path/.env"), {})


class MacFormatTests(unittest.TestCase):
    def test_formats_unseparated_hex(self):
        self.assertEqual(mac_format("aceb e638 6be4".replace(" ", "")), "AC:EB:E6:38:6B:E4")

    def test_strips_existing_separators(self):
        self.assertEqual(mac_format("ac:eb:e6:38:6b:e4"), "AC:EB:E6:38:6B:E4")

    def test_custom_separator(self):
        self.assertEqual(mac_format("aceb e638 6be4".replace(" ", ""), separator="-"), "AC-EB-E6-38-6B-E4")

    def test_invalid_length_raises(self):
        with self.assertRaises(ValueError):
            mac_format("ac:eb:e6")


class FakeWlan:
    def __init__(self, succeed_after):
        self.succeed_after = succeed_after
        self.checks = 0

    def isconnected(self):
        self.checks += 1
        return self.checks > self.succeed_after

    def connect(self, ssid, ipsk):
        pass

    def active(self, value):
        pass


class ConnectTests(unittest.TestCase):
    def test_returns_true_once_isconnected(self):
        self.assertTrue(wifi_connect.connect(FakeWlan(succeed_after=0), "ssid", "ipsk"))

    def test_polls_until_isconnected_becomes_true(self):
        real_time = wifi_connect.time
        wifi_connect.time = _FakeClock()
        try:
            self.assertTrue(wifi_connect.connect(FakeWlan(succeed_after=3), "ssid", "ipsk"))
        finally:
            wifi_connect.time = real_time


class _FakeClock:
    """Stands in for the `time` module so connect()'s poll loop advances
    instantly in tests instead of calling real time.sleep_ms()."""
    def __init__(self):
        self.now = 0

    def ticks_ms(self):
        return self.now

    def ticks_diff(self, a, b):
        return a - b

    def sleep_ms(self, ms):
        self.now += ms


if __name__ == "__main__":
    unittest.main()
