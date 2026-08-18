from __future__ import annotations

import ctypes
import logging
import sys

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


def keypress_vk(vk_code: int) -> None:
    if not sys.platform.startswith("win"):
        LOG.info("Would press Windows VK code %s (non-Windows dry run)", vk_code)
        return
    user32 = ctypes.windll.user32
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002
    user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
    user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)


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
