from __future__ import annotations

import logging
from collections import OrderedDict

from .sounds import notify_profile_switch

LOG = logging.getLogger(__name__)


class ProfileManager:
    def __init__(self, profiles_config: dict):
        self.cfg = profiles_config
        self.items = OrderedDict(profiles_config.get("items", {}))
        if not self.items:
            raise ValueError("No profiles configured")
        default = profiles_config.get("default")
        self.current_key = default if default in self.items else next(iter(self.items))

    @property
    def current(self) -> dict:
        return self.items[self.current_key]

    @property
    def current_name(self) -> str:
        return self.current.get("name", self.current_key)

    def action_for_event(self, event: str) -> str | None:
        return self.current.get("events", {}).get(event)

    def next_profile(self) -> str:
        keys = list(self.items.keys())
        idx = keys.index(self.current_key)
        self.current_key = keys[(idx + 1) % len(keys)]
        notify_profile_switch(self.cfg.get("switch_sound", {}), self.current_name)
        return self.current_key
