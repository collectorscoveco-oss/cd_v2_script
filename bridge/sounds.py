from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

LOG = logging.getLogger(__name__)


def notify_profile_switch(sound_cfg: dict, profile_name: str, profile_key: str | None = None) -> None:
    """Play a best-effort profile switch notification.

    Supported modes:
    - off: no sound
    - beep: one configured beep
    - profile_beeps: per-profile frequency/duration, fallback to beep
    - terminal_bell: terminal bell
    - file: one configured WAV file
    - profile_files: per-profile WAV file, fallback to file/beep
    - voice: Windows speech when available, fallback to beep
    - system: Windows MessageBeep when available, fallback to beep
    """
    if not sound_cfg or not sound_cfg.get("enabled", True):
        return
    mode = str(sound_cfg.get("mode", "beep"))
    if mode == "off":
        LOG.info("Profile switched to %s", profile_name)
        return

    profile_cfg = (sound_cfg.get("profiles") or {}).get(profile_key or "", {})
    try:
        if mode == "file" and sound_cfg.get("file"):
            play_sound_file(sound_cfg["file"])
        elif mode == "profile_files":
            chosen = profile_cfg.get("file") or sound_cfg.get("file")
            if chosen:
                play_sound_file(chosen)
            else:
                profile_beep(sound_cfg, profile_cfg)
        elif mode == "profile_beeps":
            profile_beep(sound_cfg, profile_cfg)
        elif mode == "voice":
            text = profile_cfg.get("voice") or f"{sound_cfg.get('voice_prefix', 'Profile')} {profile_name}"
            speak(text)
        elif mode == "terminal_bell":
            print("\a", end="", flush=True)
        elif mode == "system":
            system_sound()
        else:
            beep(int(sound_cfg.get("beep_frequency", 880)), int(sound_cfg.get("beep_duration_ms", 90)))
    except Exception as exc:  # sound should never break actions
        LOG.warning("Profile switch sound failed: %s", exc)
    LOG.info("Profile switched to %s", profile_name)


def profile_beep(sound_cfg: dict, profile_cfg: dict) -> None:
    frequency = int(profile_cfg.get("frequency", sound_cfg.get("beep_frequency", 880)))
    duration = int(profile_cfg.get("duration_ms", sound_cfg.get("beep_duration_ms", 90)))
    beep(frequency, duration)


def beep(frequency: int = 880, duration_ms: int = 90) -> None:
    if sys.platform.startswith("win"):
        import winsound
        winsound.Beep(max(37, min(32767, frequency)), max(1, duration_ms))
    else:
        print("\a", end="", flush=True)


def system_sound() -> None:
    if sys.platform.startswith("win"):
        import winsound
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    else:
        print("\a", end="", flush=True)


def speak(text: str) -> None:
    if sys.platform.startswith("win"):
        ps = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.Speak({text!r})"
        )
        subprocess.Popen(["powershell", "-NoProfile", "-Command", ps], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        LOG.info("Voice requested on non-Windows platform: %s", text)
        print("\a", end="", flush=True)


def play_sound_file(path: str) -> None:
    expanded = Path(os.path.expandvars(os.path.expanduser(path)))
    if sys.platform.startswith("win"):
        import winsound
        winsound.PlaySound(str(expanded), winsound.SND_FILENAME | winsound.SND_ASYNC)
    else:
        LOG.info("Sound file requested on non-Windows platform: %s", expanded)
