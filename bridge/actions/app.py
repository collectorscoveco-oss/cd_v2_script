from __future__ import annotations

import logging
import os
from pathlib import Path
import shlex
import subprocess
import webbrowser

LOG = logging.getLogger(__name__)


def _looks_like_protocol(command: str) -> bool:
    if "://" in command:
        return True
    # Windows app protocols such as spotify:, steam:, discord:
    return command.endswith(":") and " " not in command and "\\" not in command and "/" not in command


def _strip_wrapping_quotes(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {'"', "'"}:
        return text[1:-1].strip()
    return text


def launch(command: str) -> None:
    """Launch an app path/command robustly on Windows.

    Full .exe paths such as C:\\Users\\me\\AppData\\Roaming\\Spotify\\Spotify.exe
    should not be sent to cmd.exe unquoted; use os.startfile/subprocess directly.
    Commands with arguments still fall back to shell=True for Windows shortcuts like
    Discord's Update.exe --processStart Discord.exe.
    """
    expanded = os.path.expandvars(_strip_wrapping_quotes(command))
    LOG.info("Launching: %s", expanded)

    if _looks_like_protocol(expanded):
        open_url(expanded)
        return

    if os.name == "nt":
        # If it is a direct executable/file path, launch it directly so spaces and
        # backslashes do not get mangled by cmd.exe.
        candidate = Path(expanded)
        if candidate.exists():
            os.startfile(str(candidate))  # type: ignore[attr-defined]
            return

        # If a user pasted an .exe plus arguments, split just enough to validate the exe.
        try:
            parts = shlex.split(expanded, posix=False)
        except ValueError:
            parts = []
        if parts:
            exe = _strip_wrapping_quotes(parts[0])
            if exe.lower().endswith(".exe") and Path(exe).exists():
                subprocess.Popen(parts, shell=False)
                return

        # Final fallback keeps existing commands such as Update.exe --processStart working.
        subprocess.Popen(expanded, shell=True)
        return

    # Non-Windows dry/dev behavior.
    if Path(expanded).exists():
        subprocess.Popen([expanded])
    else:
        subprocess.Popen(shlex.split(expanded))


def open_url(url: str) -> None:
    target = os.path.expandvars(_strip_wrapping_quotes(url))
    LOG.info("Opening URL: %s", target)
    if os.name == "nt" and _looks_like_protocol(target):
        os.startfile(target)  # type: ignore[attr-defined]
        return
    webbrowser.open(target)
