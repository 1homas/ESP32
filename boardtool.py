"""
Host-side (desktop) tool for interacting with the running ESP32-C6 board over
`mpremote`, without ever re-initializing on-device objects itself — it only
reads state that boot.py/main.py already created. A fresh display init is a
~110KB contiguous allocation that's prone to MemoryError once WiFi is up (see
references/waveshare-esp32-c6-touch-lcd-1.47.md); re-triggering that just to
take a screenshot is the bug, not the fix.

CLI:
    uv run python boardtool.py screenshot out.png [--port /dev/cu.usbmodem214101]
    uv run python boardtool.py exec "print(1+1)" [--port ...]

Options:
    --port: serial port to connect to (default: auto-detect via `mpremote connect list`)
"""
__license__ = "MIT - https://mit-license.org/"

import subprocess
import sys
import zlib


class BoardError(RuntimeError):
    pass


class Board:
    def __init__(self, port: str = None):
        self.port = port or self._autodetect_port()

    def _autodetect_port(self) -> str:
        result = subprocess.run(["mpremote", "connect", "list"], capture_output=True, text=True, check=True)
        for line in result.stdout.splitlines():
            if "Espressif" in line:
                return line.split()[0]
        raise BoardError("No Espressif serial device found; pass --port explicitly")

    def _mpremote(self, *args):
        # "resume" stops mpremote's default behavior of soft-resetting the
        # board on every fresh connection (see mpremote.main.State._auto_soft_reset) -
        # without it, every exec()/screenshot() call here would silently
        # reboot boot.py/main.py before running, corrupting the very state
        # this tool exists to inspect non-invasively.
        cmd = ["mpremote", "connect", self.port, "resume", *args]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise BoardError(result.stdout + result.stderr)
        return result.stdout

    def exec(self, code: str) -> str:
        """
        Args:
            code (str): MicroPython source to run on the board
        Returns:
            str: stdout from the board
        """
        return self._mpremote("exec", code)

    def screenshot(self, out_path: str):
        """
        Save the board's currently live `display` framebuffer as a PNG.
        Raises BoardError if no `display` object exists on the board yet
        (i.e. boot.py/main.py hasn't successfully run init_display()).
        """
        dims = self.exec(
            "if 'display' not in globals():\n"
            "    raise RuntimeError('no live display object on the board')\n"
            "with open('_screenshot.bin', 'wb') as f:\n"
            "    f.write(display.buffer)\n"
            "print(display.width, display.height)\n"
        ).strip()
        width, height = (int(n) for n in dims.split())

        local_bin = out_path + ".bin"
        self._mpremote("fs", "cp", ":_screenshot.bin", local_bin)
        self._mpremote("fs", "rm", ":_screenshot.bin")

        with open(local_bin, "rb") as f:
            rgb565 = f.read()
        import os
        os.remove(local_bin)

        _write_png(out_path, rgb565, width, height)


def _write_png(path: str, rgb565: bytes, width: int, height: int):
    """
    Encode little-endian RGB565 framebuffer bytes (the JD9853 driver's buffer
    byte order) as an 8-bit truecolor PNG, using only the standard library
    (no Pillow dependency).
    """
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter type: none
        row_start = y * width * 2
        for x in range(width):
            i = row_start + x * 2
            value = (rgb565[i + 1] << 8) | rgb565[i]
            r5 = (value >> 11) & 0x1F
            g6 = (value >> 5) & 0x3F
            b5 = value & 0x1F
            raw.append((r5 * 255) // 31)
            raw.append((g6 * 255) // 63)
            raw.append((b5 * 255) // 31)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            len(data).to_bytes(4, "big")
            + tag
            + data
            + zlib.crc32(tag + data).to_bytes(4, "big")
        )

    ihdr = (
        width.to_bytes(4, "big")
        + height.to_bytes(4, "big")
        + bytes([8, 2, 0, 0, 0])  # bit depth, color type (truecolor), compression, filter, interlace
    )
    idat = zlib.compress(bytes(raw))

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", idat))
        f.write(chunk(b"IEND", b""))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    p_shot = sub.add_parser("screenshot")
    p_shot.add_argument("out_path")

    p_exec = sub.add_parser("exec")
    p_exec.add_argument("code")

    args = parser.parse_args()
    board = Board(args.port)

    if args.command == "screenshot":
        board.screenshot(args.out_path)
        print(f"Saved {args.out_path}")
    elif args.command == "exec":
        print(board.exec(args.code), end="")
