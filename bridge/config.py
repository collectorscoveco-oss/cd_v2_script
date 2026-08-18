import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG = ROOT / "config.example.json"
USER_CONFIG = ROOT / "config.json"


def ensure_config(path: Path | None = None) -> Path:
    target = path or USER_CONFIG
    if not target.exists():
        shutil.copyfile(DEFAULT_CONFIG, target)
    return target


def load_config(path: str | Path | None = None) -> dict:
    target = ensure_config(Path(path) if path else None)
    with target.open("r", encoding="utf-8") as f:
        config = json.load(f)
    changed = migrate_config(config)
    if changed:
        save_config(config, target)
    return config


def migrate_config(config: dict) -> bool:
    """Apply safe additive config migrations for existing local configs."""
    changed = False
    actions = config.setdefault("actions", {})
    app_actions = actions.setdefault("app", {})
    open_actions = app_actions.setdefault("open", {})
    if open_actions.get("spotify") != "spotify:":
        open_actions["spotify"] = "spotify:"
        changed = True

    profiles = config.get("profiles", {}).get("items", {})
    for item in profiles.values():
        events = item.setdefault("events", {})
        labels = item.setdefault("labels", {})
        for event, action in list(events.items()):
            if action == "app.launch.spotify":
                events[event] = "app.open.spotify"
                changed = True

        if events.get("BTN_10_PRESS") != "media.play_pause":
            events["BTN_10_PRESS"] = "media.play_pause"
            changed = True
        if events.get("BTN_10_LONG") != "profile.next":
            events["BTN_10_LONG"] = "profile.next"
            changed = True
        if "BTN_08_LONG" in events:
            events.pop("BTN_08_LONG", None)
            changed = True
        if labels.get("BTN_10_PRESS") != "Play/Pause":
            labels["BTN_10_PRESS"] = "Play/Pause"
            changed = True
        if labels.get("BTN_10_LONG") != "Hold: Next Page":
            labels["BTN_10_LONG"] = "Hold: Next Page"
            changed = True
    return changed


def save_config(config: dict, path: str | Path | None = None) -> Path:
    target = Path(path) if path else USER_CONFIG
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")
    return target
