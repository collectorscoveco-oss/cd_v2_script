from __future__ import annotations

import logging
import sys

LOG = logging.getLogger(__name__)

# Minimal optional hotkey support. For serious hotkeys, install/use a dedicated package later.
VK = {
    "ctrl": 0x11, "control": 0x11, "shift": 0x10, "alt": 0x12,
    "m": 0x4D, "d": 0x44, "f13": 0x7C, "f14": 0x7D, "f15": 0x7E,
}


def press(keys: list[str]) -> None:
    if not sys.platform.startswith("win"):
        LOG.info("Would press hotkey %s (non-Windows dry run)", "+".join(keys))
        return
    import ctypes
    user32 = ctypes.windll.user32
    KEYUP = 0x0002
    codes = [VK[k.lower()] for k in keys]
    for code in codes:
        user32.keybd_event(code, 0, 0, 0)
    for code in reversed(codes):
        user32.keybd_event(code, 0, KEYUP, 0)
