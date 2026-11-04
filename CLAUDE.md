# ESP32 Project

## Hardware

The board in this project is a **Waveshare ESP32-C6-Touch-LCD-1.47** (sold on Amazon as
"ESP32-C6 1.47inch Touch Display Development Board"). Before writing or debugging any
display/touch/SD-card code, read:

- `references/waveshare-esp32-c6-touch-lcd-1.47.md` — confirmed GPIO pin mapping (LCD, touch,
  IMU, SD card), driver chip (JD9853, not ST7789), and known gotchas.
- `references/waveshare-esp32-c6-lcd-1.47.md` — the **sibling non-touch board**, kept only as a
  contrast reference. Its pin numbers (e.g. GPIO22 = backlight) do NOT apply to this project's
  board (where GPIO22 = LCD_RST, GPIO23 = backlight). Do not reuse its pin numbers.

Do not re-derive pin numbers from Waveshare's wiki prose or Arduino code snippets — those have
been observed to blend in pin numbers from unrelated board variants (e.g. ESP32-S3 GPIO numbers
appearing in C6 documentation). Pull pin numbers from the schematic PDF's netlist text for the
exact product name instead.

## Workflow notes

- Flash/erase ESP32 flash via `esptool`, run on-device code via `mpremote`, both installed through
  `uv` (see README.md Setup).
- Use MicroPython **v1.29.0+** on this board. v1.26.1's WiFi stack is broken here (`wlan.scan()`
  returns nothing, `wlan.connect()` raises `OSError: Wifi Internal Error`) — see
  `references/waveshare-esp32-c6-touch-lcd-1.47.md`.
- The LCD driver is [mattytrentini/micropython-jd9853](https://github.com/mattytrentini/micropython-jd9853)
  (purpose-built for this exact board/chip), installed via
  `mpremote mip install --target lib github:mattytrentini/micropython-jd9853`. Do not use
  `russhughes/st7789py_mpy` here — this panel's driver chip is JD9853, not ST7789.
- After flashing or running several test scripts in one `mpremote` session, re-initializing the
  display can throw `MemoryError` from heap fragmentation — power-cycle or `mpremote reset` first.
- **Testing over `mpremote exec`/raw REPL does not prove real power-on boot behavior.** It attaches
  to an already-running MicroPython image, which has a very different (much less fragmented) heap
  than a true `boot.py` auto-run on reset. Code that works fine pasted interactively can still fail
  with `MemoryError` on an actual reset. Validate boot.py changes with `mpremote reset` + a
  `crash.log`/diagnostic file read afterward, not with `boardtool.py exec`.
- **Never use `machine.reset()` as a MemoryError retry mechanism without an escape hatch you've
  verified works.** It was tried here (RTC-memory-backed retry counter, to survive the reset) and
  the board got stuck resetting in a loop, unrecoverable via `mpremote` (every connection attempt
  raced the next reset). Recovery required `esptool erase_flash` + reflash — the same thing you'd
  need if the device were bricked. If a MemoryError retry can't be proven to terminate, fail soft
  (return `None`/continue without the resource) instead of resetting.

## Lessons learned: WiFi + display, v2 (heap fragmentation, 2026-11-03)

The v1 rebuild below was sound in design but had never actually been validated end-to-end on real
hardware — it was sitting in `Archive/` with no record of a successful boot. Restoring it and
testing for real surfaced two unrelated problems, both initially (and wrongly) blamed on "the
code is garbage": a real screenshot-tool bug, and a genuine, severe heap-fragmentation problem
specific to `boot.py` running standalone.

- **`boardtool.py`'s screenshot capture had the framebuffer byte order backwards.** It decoded the
  JD9853 driver's RGB565 buffer as big-endian; the driver actually stores it little-endian. Filling
  the screen red and screenshotting it rendered as dark blue — this alone was enough to convince an
  earlier debugging session the *display* was broken, when the display was fine and only the
  diagnostic tool was wrong. Fixed in `_write_png()`, with `test_boardtool.py` updated to assert
  little-endian input. **Lesson: before concluding a driver/rendering bug, check whether the thing
  reporting the bug (a screenshot tool, a log parser) is itself correct** — verify it against a
  known-good case first.
- **The WiFi "wrong password" (`STAT_WRONG_PASSWORD`) turned out to be AP-side**, not a bug in
  `wifi_connect.connect()` — confirmed by the exact same code working once the network-side IPSK
  registration was fixed. Don't assume client-side code is broken just because a previous session
  couldn't get it working; get a precise on-device error code (`wlan.status()`) before rewriting.
- **The display's ~110KB framebuffer allocation is right at the edge of what this board's heap can
  reliably supply, and the margin is not meaningfully under your control from `boot.py`'s source.**
  Confirmed on-device, exhaustively:
  - Total free heap during the failure is typically 160-165KB (plenty), but the *largest
    contiguous* free block is as little as ~109,851 bytes — about 230 bytes short of the 110,080
    needed. This is fragmentation, not exhaustion.
  - `import network` alone (before even activating WiFi) can cost ~170KB of heap due to the WiFi
    driver's internal buffers. Doing it after `init_display()` helps, but isn't sufficient by itself.
  - MicroPython compiles a whole `.py` file's bytecode upfront, before executing line 1 — so code
    placed *after* `init_display()` in `boot.py`'s source still competes for heap *before* that
    call runs. This is why the WiFi-connect logic was moved into `wifi_connect.boot_connect()`,
    imported only after display init succeeds, rather than written inline in `boot.py`.
  - Whether the allocation succeeds was observed to vary run-to-run with no code change — tied to
    incidental factors (flash/filesystem fragmentation state, timing) outside `boot.py`'s control.
    A full `esptool erase_flash` + reflash measurably improves (but does not guarantee) success.
  - **Net effect: expect this allocation to intermittently fail even in working code.** The shipped
    design (`boot.py`'s `_init_display_retry()`) retries in-process (gc.collect + allocate/free
    churn through decreasing sizes) a few times, then gives up and continues with `display = None`
    rather than crashing — WiFi still comes up fine either way, and `wifi_connect.boot_connect()` /
    `main.py` both handle `display is None`. Do not "fix" an occasional display-less boot by adding
    more retry logic to `boot.py` itself; more code there is more bytecode competing for the same
    allocation, which was observed to make failures *more* likely, not less.

## Lessons learned: WiFi + display, v1 (rebuilt from scratch 2026-11-03)

The first implementation added a touch-driven connect/disconnect toggle (`touch.py` AXS5106L
driver + `gestures.py` tap/hold/swipe state machine + `progress.py` progress bar) on top of the
WiFi connect logic, split across `boot.py` (one-shot setup) and `main.py` (the poll loop), with
`main.py` relying on variables (`display`, `wlan`, `env`, `connected`, `connect_started_ms`,
`MAX_RETRIES`, `TIMEOUT`) left over in `boot.py`'s globals rather than passing them explicitly.
The actual requirement was much smaller — connect on boot, show connected/disconnected — and the
extra moving parts made failures hard to localize (display bug? touch bug? gesture timing bug?
WiFi bug? shared-globals bug?) without a serial console to debug any of it live.

Rebuilt with touch/gestures/progress removed entirely. `boot.py` now does setup + one blocking
connect attempt; `main.py` just polls `wlan.isconnected()` and updates the display on change,
reconnecting if the link drops. No shared mutable state beyond `display`, `wlan`, and `env`.

- **Implicit cross-file globals are a debugging trap on a device with no serial console.** When
  `main.py` fails, the question "was `connected` stale, or never set, or shadowed?" can't be
  answered by inspection — there's no REPL attached once it's running standalone. Prefer each file
  re-deriving state from `wlan.isconnected()` directly over trusting a value a *different* file
  set earlier in the shared namespace.
- **Don't add interaction (touch/gestures) to a status display unless asked.** It roughly
  triples the surface area that can break (I2C driver timing, gesture state machine edge cases,
  display redraw timing) for a feature nobody requested. Start with the minimum that satisfies
  the stated goal; add interaction only when explicitly asked for.
- **`pyproject.toml`/`requirements.txt` listed `machine` and `network` as pip dependencies**,
  presumably intended as desktop-side stubs for MicroPython's built-in modules so hardware code
  could be unit-tested off-device. They're actually unrelated PyPI packages with those generic
  names (a chat-networking library and an unrelated `machine` package) — installing them silently
  shadows the real MicroPython modules' API with garbage, so `import network` on desktop gets
  something with no `STAT_IDLE`/`WLAN`/etc. Removed both from `pyproject.toml` and
  `requirements.txt`. There is no real desktop stub for `network`/`machine`/`framebuf` — code that
  touches them (`wifi_connect.connect()`, all of `display.py`) is validated on-device via
  `mpremote`, not via `uv run pytest`. Only pure-logic helpers with no hardware import
  (`load_dotenv`, `mac_format`) get desktop unit tests.
- **Duplicate near-identical functions drift.** The old `wifi_connect.py` had both
  `wlan_connect()` and `wifi_connect()` — one with the OSError-retry workaround, one without —
  and it was easy to end up calling the wrong one. Rebuilt with a single `connect()`.
- Keep allocating the display (`init_display()`) *before* activating WiFi — still the right order,
  but see the v2 section above: it helps, it doesn't guarantee success.
