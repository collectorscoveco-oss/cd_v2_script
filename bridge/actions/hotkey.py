from __future__ import annotations

import ctypes
import logging
import string
import sys
import time
from ctypes import wintypes

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


def _window_title(hwnd: int) -> str:
    user32 = ctypes.windll.user32
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def focus_window_title_contains(title_part: str) -> bool:
    """Bring a visible window whose title contains title_part to the foreground.

    This is intentionally title-based to avoid a pywin32 dependency. It fixes the
    browser-focused virtual deck case: click button in Chrome -> focus Discord ->
    send Discord hotkey, instead of Chrome consuming the shortcut.
    """
    if not sys.platform.startswith("win"):
        LOG.info("Would focus window containing %r (non-Windows dry run)", title_part)
        return False

    user32 = ctypes.windll.user32
    matches: list[int] = []
    needle = title_part.lower()

    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        title = _window_title(hwnd)
        if title and needle in title.lower():
            matches.append(int(hwnd))
            return False
        return True

    user32.EnumWindows(WNDENUMPROC(callback), 0)
    if not matches:
        LOG.warning("No visible window found containing %r", title_part)
        return False

    hwnd = matches[0]
    SW_RESTORE = 9
    user32.ShowWindow(hwnd, SW_RESTORE)
    time.sleep(0.08)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.12)
    return True


def press(keys: list[str], focus_title: str | None = None) -> None:
    normalized = [key.strip().lower() for key in keys if key and key.strip()]
    if not normalized:
        raise ValueError("Hotkey action has no keys configured")
    if not sys.platform.startswith("win"):
        LOG.info("Would press hotkey %s (non-Windows dry run)", "+".join(normalized))
        return

    if focus_title:
        focus_window_title_contains(focus_title)

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
