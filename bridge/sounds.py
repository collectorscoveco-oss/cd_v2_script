from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

LOG = logging.getLogger(__name__)


def notify_profile_switch(sound_cfg: dict, profile_name: str) -> None:
    if not sound_cfg or not sound_cfg.get("enabled", True):
        return
    mode = sound_cfg.get("mode", "beep")
    try:
        if mode == "file" and sound_cfg.get("file"):
            play_sound_file(sound_cfg["file"])
        elif mode == "terminal_bell":
            print("\a", end="", flush=True)
        else:
            beep(int(sound_cfg.get("beep_frequency", 880)), int(sound_cfg.get("beep_duration_ms", 90)))
    except Exception as exc:  # sound should never break actions
        LOG.warning("Profile switch sound failed: %s", exc)
    LOG.info("Profile switched to %s", profile_name)


def beep(frequency: int = 880, duration_ms: int = 90) -> None:
    if sys.platform.startswith("win"):
        import winsound
        winsound.Beep(frequency, duration_ms)
    else:
        print("\a", end="", flush=True)


def play_sound_file(path: str) -> None:
    expanded = Path(os.path.expandvars(os.path.expanduser(path)))
    if sys.platform.startswith("win"):
        import winsound
        winsound.PlaySound(str(expanded), winsound.SND_FILENAME | winsound.SND_ASYNC)
    else:
        LOG.info("Sound file requested on non-Windows platform: %s", expanded)
