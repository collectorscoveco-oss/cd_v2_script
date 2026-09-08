from __future__ import annotations

import ctypes
import logging
import sys
import time
from ctypes import wintypes

LOG = logging.getLogger(__name__)

VK_CODES = {
    "volume_mute": 0xAD,
    "volume_down": 0xAE,
    "volume_up": 0xAF,
    "media_next": 0xB0,
    "media_previous": 0xB1,
    "media_stop": 0xB2,
    "media_play_pause": 0xB3,
}

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
INPUT_KEYBOARD = 1


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]


def send_input_vk(vk_code: int, *, extended: bool = True) -> None:
    """Send one virtual-key press using SendInput.

    keybd_event works for some systems but can be ignored by media players and
    native shells. SendInput is the modern Windows path and is more reliable for
    media keys like Play/Pause.
    """
    if not sys.platform.startswith("win"):
        LOG.info("Would press Windows VK code %s (non-Windows dry run)", vk_code)
        return

    user32 = ctypes.windll.user32
    scan = user32.MapVirtualKeyW(vk_code, 0)
    extra = ctypes.c_ulong(0)
    flags = KEYEVENTF_EXTENDEDKEY if extended else 0
    inputs = (INPUT * 2)(
        INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=KEYBDINPUT(vk_code, scan, flags, 0, ctypes.pointer(extra)))),
        INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=KEYBDINPUT(vk_code, scan, flags | KEYEVENTF_KEYUP, 0, ctypes.pointer(extra)))),
    )
    sent = user32.SendInput(2, ctypes.byref(inputs), ctypes.sizeof(INPUT))
    if sent != 2:
        raise OSError(f"SendInput sent {sent} of 2 keyboard events")
    time.sleep(0.03)


def keypress_vk(vk_code: int) -> None:
    send_input_vk(vk_code, extended=True)


def volume_up() -> None:
    keypress_vk(VK_CODES["volume_up"])


def volume_down() -> None:
    keypress_vk(VK_CODES["volume_down"])


def mute() -> None:
    keypress_vk(VK_CODES["volume_mute"])


def media_play_pause() -> None:
    keypress_vk(VK_CODES["media_play_pause"])


def media_next() -> None:
    keypress_vk(VK_CODES["media_next"])


def media_previous() -> None:
    keypress_vk(VK_CODES["media_previous"])
