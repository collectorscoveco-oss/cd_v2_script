from __future__ import annotations

import logging
import os
import shlex
import subprocess
import webbrowser

LOG = logging.getLogger(__name__)


def launch(command: str) -> None:
    expanded = os.path.expandvars(command)
    LOG.info("Launching: %s", expanded)
    if os.name == "nt":
        subprocess.Popen(expanded, shell=True)
    else:
        subprocess.Popen(shlex.split(expanded))


def open_url(url: str) -> None:
    LOG.info("Opening URL: %s", url)
    webbrowser.open(url)
