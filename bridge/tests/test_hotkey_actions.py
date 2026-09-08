import sys

import pytest

from bridge.actions import hotkey


def test_hotkey_supports_discord_and_obs_defaults():
    for key in ["ctrl", "shift", "m", "alt", "1", "2", "r", "s", "f13", "f24"]:
        assert isinstance(hotkey.vk_for_key(key), int)


def test_unsupported_hotkey_has_clear_error():
    with pytest.raises(KeyError, match="Unsupported hotkey key"):
        hotkey.vk_for_key("definitely-not-a-key")


def test_hotkey_non_windows_dry_run_does_not_press(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    hotkey.press(["ctrl", "shift", "m"])


def test_focus_window_non_windows_is_safe(monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    assert hotkey.focus_window_title_contains("Discord") is False
