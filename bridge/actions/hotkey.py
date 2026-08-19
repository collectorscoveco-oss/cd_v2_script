from __future__ import annotations

import logging
import string
import sys
import time

LOG = logging.getLogger(__name__)

MODIFIER_VK = {
    "ctrl": 0x11,
    "control": 0x11,
    "shift": 0x10,
    "alt": 0x12,
    "win": 0x5B,
    "windows": 0x5B,
    "cmd": 0x5B,
}

NAMED_VK = {
    "space": 0x20,
    "tab": 0x09,
    "enter": 0x0D,
    "return": 0x0D,
    "escape": 0x1B,
    "esc": 0x1B,
    "backspace": 0x08,
    "delete": 0x2E,
    "insert": 0x2D,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "left": 0x25,
    "up": 0x26,
    "right": 0x27,
    "down": 0x28,
}

VK = {
    **MODIFIER_VK,
    **NAMED_VK,
    **{letter: ord(letter.upper()) for letter in string.ascii_lowercase},
    **{str(number): ord(str(number)) for number in range(10)},
    **{f"f{number}": 0x6F + number for number in range(1, 25)},
}


def vk_for_key(key: str) -> int:
    normalized = key.strip().lower().replace(" ", "")
    if normalized not in VK:
        raise KeyError(f"Unsupported hotkey key: {key}. Add it to bridge/actions/hotkey.py")
    return VK[normalized]


def press(keys: list[str]) -> None:
    normalized = [key.strip().lower() for key in keys if key and key.strip()]
    if not normalized:
        raise ValueError("Hotkey action has no keys configured")
    if not sys.platform.startswith("win"):
        LOG.info("Would press hotkey %s (non-Windows dry run)", "+".join(normalized))
        return
    import ctypes

    user32 = ctypes.windll.user32
    KEYEVENTF_KEYUP = 0x0002
    codes = [vk_for_key(key) for key in normalized]
    for code in codes:
        user32.keybd_event(code, 0, 0, 0)
        time.sleep(0.025)
    time.sleep(0.075)
    for code in reversed(codes):
        user32.keybd_event(code, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.025)
