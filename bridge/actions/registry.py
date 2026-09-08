from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable

from . import app as app_actions
from . import hotkey as hotkey_actions
from . import windows as win_actions
from .sonar import SonarClient

LOG = logging.getLogger(__name__)


@dataclass
class ActionContext:
    config: dict
    profile_manager: object
    sonar_client: SonarClient | None = None


class ActionRegistry:
    def __init__(self, context: ActionContext):
        self.ctx = context
        sonar_cfg = context.config.get("actions", {}).get("sonar", {})
        self.ctx.sonar_client = SonarClient(sonar_cfg)

    def execute(self, action_name: str) -> None:
        LOG.info("Executing action: %s", action_name)
        if action_name == "profile.next":
            self.ctx.profile_manager.next_profile()
            return
        if action_name.startswith("windows."):
            self._windows(action_name.split(".", 1)[1])
            return
        if action_name.startswith("media."):
            self._media(action_name.split(".", 1)[1])
            return
        if action_name.startswith("app.launch."):
            key = action_name.split(".", 2)[2]
            command = self.ctx.config.get("actions", {}).get("app", {}).get("launch", {}).get(key)
            if not command:
                raise KeyError(f"No app launch command configured for {key}")
            app_actions.launch(command)
            return
        if action_name.startswith("app.open."):
            key = action_name.split(".", 2)[2]
            url = self.ctx.config.get("actions", {}).get("app", {}).get("open", {}).get(key)
            if not url:
                raise KeyError(f"No app open URL configured for {key}")
            app_actions.open_url(url)
            return
        if action_name.startswith("hotkey."):
            key = action_name.split(".", 1)[1]
            keys = self.ctx.config.get("actions", {}).get("hotkey", {}).get(key)
            if not keys:
                raise KeyError(f"No hotkey configured for {key}")
            focus_cfg = self.ctx.config.get("actions", {}).get("hotkey_focus", {}).get(key)
            if focus_cfg is True:
                focus_title = "Discord" if key == "discord_mute" else None
            elif isinstance(focus_cfg, str) and focus_cfg.strip():
                focus_title = focus_cfg.strip()
            else:
                focus_title = None
            hotkey_actions.press(keys, focus_title=focus_title)
            return
        if action_name.startswith("sonar."):
            self._sonar(action_name)
            return
        raise KeyError(f"Unknown action: {action_name}")

    def _windows(self, name: str) -> None:
        mapping: dict[str, Callable[[], None]] = {
            "volume_up": win_actions.volume_up,
            "volume_down": win_actions.volume_down,
            "mute": win_actions.mute,
        }
        mapping[name]()

    def _media(self, name: str) -> None:
        mapping: dict[str, Callable[[], None]] = {
            "play_pause": win_actions.media_play_pause,
            "next": win_actions.media_next,
            "previous": win_actions.media_previous,
        }
        mapping[name]()

    def _sonar(self, action_name: str) -> None:
        client = self.ctx.sonar_client
        if client is None:
            raise RuntimeError("Sonar client was not initialized")
        parts = action_name.split(".")
        if len(parts) == 3 and parts[2] == "volume_up":
            client.volume_up(parts[1]); return
        if len(parts) == 3 and parts[2] == "volume_down":
            client.volume_down(parts[1]); return
        if len(parts) == 3 and parts[2] == "toggle_mute":
            client.toggle_mute(parts[1]); return
        if len(parts) == 3 and parts[2] == "mute":
            client.set_channel_mute(parts[1], True); return
        if len(parts) == 3 and parts[2] == "unmute":
            client.set_channel_mute(parts[1], False); return
        if action_name == "sonar.output.rotate":
            client.rotate_output(); return
        raise KeyError(f"Unknown Sonar action: {action_name}")
