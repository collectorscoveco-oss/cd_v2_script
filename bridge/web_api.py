from __future__ import annotations

import json
import logging
import subprocess
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .actions.registry import ActionContext, ActionRegistry
from .config import load_config, save_config
from .main import handle_event, setup_logging
from .profiles import ProfileManager

BUTTON_EVENTS = [f"BTN_{idx:02d}_PRESS" for idx in range(1, 11)]
SPECIAL_EVENTS = ["BTN_10_LONG"]
ENCODER_EVENTS = ["ENC_01_CCW", "ENC_01_PRESS", "ENC_01_CW"]

CATEGORY_COLORS = {
    "Sonar": "#32d3ff",
    "Windows": "#94a3b8",
    "Media": "#22c55e",
    "App": "#ff9f43",
    "Website": "#38bdf8",
    "Hotkey": "#8b5cf6",
    "Profile": "#facc15",
    "Other": "#64748b",
}

THEMES = {
    "sonar": {"accent": "#32d3ff", "panel": "#102635"},
    "apps": {"accent": "#ff9f43", "panel": "#2d2115"},
    "gaming": {"accent": "#8b5cf6", "panel": "#211936"},
    "streaming": {"accent": "#ef4444", "panel": "#321819"},
    "music": {"accent": "#22c55e", "panel": "#143121"},
    "desktop": {"accent": "#94a3b8", "panel": "#222833"},
}

ACTION_LABELS = {
    "profile.next": "Switch Page",
    "windows.volume_up": "Windows Vol +",
    "windows.volume_down": "Windows Vol -",
    "windows.mute": "Windows Mute",
    "media.play_pause": "Play/Pause",
    "media.next": "Media Next",
    "media.previous": "Media Prev",
    "sonar.game.volume_up": "Game +",
    "sonar.game.volume_down": "Game -",
    "sonar.game.toggle_mute": "Game Mute",
    "sonar.chat.volume_up": "Chat +",
    "sonar.chat.volume_down": "Chat -",
    "sonar.chat.toggle_mute": "Chat Mute",
    "sonar.media.volume_up": "Media +",
    "sonar.media.volume_down": "Media -",
    "sonar.media.toggle_mute": "Media Mute",
    "sonar.aux.volume_up": "Aux +",
    "sonar.aux.volume_down": "Aux -",
    "sonar.aux.toggle_mute": "Aux Mute",
    "sonar.mic.volume_up": "Mic +",
    "sonar.mic.volume_down": "Mic -",
    "sonar.mic.toggle_mute": "Mic Mute Toggle",
    "sonar.mic.mute": "Mic Mute",
    "sonar.mic.unmute": "Mic Unmute",
    "hotkey.discord_mute": "Discord Mute",
    "hotkey.obs_scene_1": "OBS Scene 1",
    "hotkey.obs_scene_2": "OBS Scene 2",
    "hotkey.obs_record": "OBS Record",
    "hotkey.obs_stream": "OBS Stream",
    "app.launch.discord": "Open Discord",
    "app.launch.steelseries_gg": "Open GG",
    "app.launch.bambu_studio": "Open Bambu",
    "app.launch.obs": "Open OBS",
    "app.launch.spotify": "Open Spotify EXE",
    "app.open.spotify": "Open Spotify",
    "app.open.youtube": "Open YouTube",
}


def action_target(config: dict, action: str | None) -> str:
    if not action:
        return ""
    if action.startswith("app.launch."):
        key = action.split(".", 2)[2]
        return str(config.get("actions", {}).get("app", {}).get("launch", {}).get(key, ""))
    if action.startswith("app.open."):
        key = action.split(".", 2)[2]
        return str(config.get("actions", {}).get("app", {}).get("open", {}).get(key, ""))
    return ""


def action_category(action: str | None, config: dict | None = None) -> str:
    if not action:
        return "Other"
    if action.startswith("sonar."):
        return "Sonar"
    if action.startswith("windows."):
        return "Windows"
    if action.startswith("media."):
        return "Media"
    if action.startswith("app.open."):
        target = action_target(config or {}, action).lower()
        if target.endswith(":") and not target.startswith(("http:", "https:")):
            return "App"
        return "Website"
    if action.startswith("app."):
        return "App"
    if action.startswith("hotkey."):
        return "Hotkey"
    if action.startswith("profile."):
        return "Profile"
    return "Other"


def action_label(action: str | None) -> str:
    if not action:
        return "Unmapped"
    if action in ACTION_LABELS:
        return ACTION_LABELS[action]
    if action.startswith("app.launch.") or action.startswith("app.open."):
        return "Open " + action.rsplit(".", 1)[-1].replace("_", " ").title()
    if action.startswith("hotkey."):
        return "Hotkey " + action.rsplit(".", 1)[-1].replace("_", " ").title()
    return action.replace(".", " ")


def available_actions(config: dict) -> list[dict]:
    actions = set(ACTION_LABELS)
    for key in config.get("actions", {}).get("app", {}).get("launch", {}):
        actions.add(f"app.launch.{key}")
    for key in config.get("actions", {}).get("app", {}).get("open", {}):
        actions.add(f"app.open.{key}")
    for key in config.get("actions", {}).get("hotkey", {}):
        actions.add(f"hotkey.{key}")
    return [
        {
            "id": action,
            "label": action_label(action),
            "category": action_category(action, config),
            "target": action_target(config, action),
            "editableTarget": action.startswith(("app.launch.", "app.open.")),
        }
        for action in sorted(actions)
    ]


class SonarDeckApiState:
    def __init__(self, config_path: str | None = None):
        self.config_path = config_path
        self.config = load_config(config_path)
        setup_logging(self.config)
        self.profiles = ProfileManager(self.config["profiles"])
        self.registry = ActionRegistry(ActionContext(config=self.config, profile_manager=self.profiles))
        self.lock = threading.Lock()
        self.log: list[str] = [f"Modern UI bridge ready. Active page: {self.profiles.current_name}"]

    def reload(self) -> None:
        self.config = load_config(self.config_path)
        self.profiles = ProfileManager(self.config["profiles"])
        self.registry = ActionRegistry(ActionContext(config=self.config, profile_manager=self.profiles))

    def append_log(self, message: str) -> None:
        self.log.append(message)
        self.log = self.log[-80:]
        logging.getLogger("sonardeck.web").info(message)

    def snapshot(self) -> dict:
        current_key = str(self.profiles.current_key)
        current = self.config["profiles"]["items"].get(current_key, {})
        events = current.get("events", {})
        labels = current.get("labels", {})
        icons = current.get("icons", {})
        colors = current.get("colors", {})
        buttons = []
        for idx, event in enumerate(BUTTON_EVENTS, start=1):
            action = events.get(event)
            category = action_category(action, self.config)
            buttons.append(
                {
                    "index": idx,
                    "event": event,
                    "action": action,
                    "label": labels.get(event) or action_label(action),
                    "category": category,
                    "target": action_target(self.config, action),
                    "icon": icons.get(event, ""),
                    "color": colors.get(event) or CATEGORY_COLORS.get(category, CATEGORY_COLORS["Other"]),
                    "autoColor": CATEGORY_COLORS.get(category, CATEGORY_COLORS["Other"]),
                    "customColor": colors.get(event, ""),
                }
            )
        encoder = []
        for event in ENCODER_EVENTS:
            action = events.get(event)
            encoder.append({"event": event, "action": action, "label": action_label(action)})
        specials = []
        for event in SPECIAL_EVENTS:
            action = events.get(event)
            specials.append({"event": event, "action": action, "label": labels.get(event) or action_label(action)})
        return {
            "profile": {"key": current_key, "name": self.profiles.current_name, "theme": THEMES.get(current_key, THEMES["desktop"])},
            "profiles": [{"key": key, "name": item.get("name", key)} for key, item in self.config["profiles"].get("items", {}).items()],
            "buttons": buttons,
            "encoder": encoder,
            "specials": specials,
            "actions": available_actions(self.config),
            "log": self.log,
        }

    def fire(self, event: str) -> dict:
        with self.lock:
            before = str(self.profiles.current_key)
            handle_event(event, self.profiles, self.registry)
            after = str(self.profiles.current_key)
            self.append_log(f"{event}: {before} -> {after}")
            return self.snapshot()

    def set_profile(self, profile: str) -> dict:
        with self.lock:
            if profile not in self.profiles.items:
                raise ValueError(f"Unknown profile: {profile}")
            self.profiles.current_key = profile
            self.append_log(f"Switched page to {self.profiles.current_name}")
            return self.snapshot()

    def save_label(self, profile: str, event: str, label: str) -> dict:
        with self.lock:
            item = self.config["profiles"]["items"].setdefault(profile, {})
            labels = item.setdefault("labels", {})
            if label.strip():
                labels[event] = label.strip()
            else:
                labels.pop(event, None)
            save_config(self.config, self.config_path)
            self.reload()
            self.profiles.current_key = profile
            self.append_log(f"Saved display name: {profile} {event} -> {label or '(auto)'}")
            return self.snapshot()

    def save_icon(self, profile: str, event: str, icon: str) -> dict:
        with self.lock:
            item = self.config["profiles"]["items"].setdefault(profile, {})
            icons = item.setdefault("icons", {})
            clean_icon = icon.strip()
            if clean_icon:
                icons[event] = clean_icon
            else:
                icons.pop(event, None)
            save_config(self.config, self.config_path)
            self.reload()
            self.profiles.current_key = profile
            self.append_log(f"Saved icon: {profile} {event} -> {clean_icon or 'Auto'}")
            return self.snapshot()

    def save_color(self, profile: str, event: str, color: str) -> dict:
        with self.lock:
            item = self.config["profiles"]["items"].setdefault(profile, {})
            colors = item.setdefault("colors", {})
            clean_color = color.strip()
            if clean_color:
                if not (clean_color.startswith("#") and len(clean_color) == 7):
                    raise ValueError("Button color must be a hex color like #8b5cf6")
                colors[event] = clean_color
            else:
                colors.pop(event, None)
            save_config(self.config, self.config_path)
            self.reload()
            self.profiles.current_key = profile
            self.append_log(f"Saved color: {profile} {event} -> {clean_color or 'Auto'}")
            return self.snapshot()

    def save_mapping(self, profile: str, event: str, action: str, label: str | None = None) -> dict:
        with self.lock:
            item = self.config["profiles"]["items"].setdefault(profile, {})
            events = item.setdefault("events", {})
            labels = item.setdefault("labels", {})
            if action.strip():
                events[event] = action.strip()
            else:
                events.pop(event, None)
            if label is not None:
                if label.strip():
                    labels[event] = label.strip()
                else:
                    labels.pop(event, None)
            save_config(self.config, self.config_path)
            self.reload()
            self.profiles.current_key = profile
            self.append_log(f"Saved mapping: {profile} {event} -> {action or '(unmapped)'}")
            return self.snapshot()

    def add_app_action(self, key: str, label: str, command: str, profile: str = "", event: str = "", kind: str = "launch") -> dict:
        with self.lock:
            clean_key = "".join(ch if ch.isalnum() else "_" for ch in key.strip().lower()).strip("_")
            if not clean_key:
                raise ValueError("Action key is required, for example: spotify or discord")
            clean_command = command.strip().strip('"')
            if not clean_command:
                raise ValueError("App path, URL, or protocol is required")
            actions = self.config.setdefault("actions", {})
            app_actions = actions.setdefault("app", {})
            is_open = kind == "open" or clean_command.startswith(("http://", "https://")) or (clean_command.endswith(":") and ":\\" not in clean_command)
            bucket = "open" if is_open else "launch"
            app_actions.setdefault(bucket, {})[clean_key] = clean_command
            action_id = f"app.{bucket}.{clean_key}"
            if profile and event:
                item = self.config["profiles"]["items"].setdefault(profile, {})
                item.setdefault("events", {})[event] = action_id
                if label.strip():
                    item.setdefault("labels", {})[event] = label.strip()
            save_config(self.config, self.config_path)
            self.reload()
            if profile:
                self.profiles.current_key = profile
            self.append_log(f"Added app action: {action_id} -> {clean_command}")
            return self.snapshot()

    def update_action_target(self, action: str, target: str) -> dict:
        with self.lock:
            clean_target = target.strip().strip('"')
            if action.startswith("app.launch."):
                key = action.split(".", 2)[2]
                self.config.setdefault("actions", {}).setdefault("app", {}).setdefault("launch", {})[key] = clean_target
            elif action.startswith("app.open."):
                key = action.split(".", 2)[2]
                self.config.setdefault("actions", {}).setdefault("app", {}).setdefault("open", {})[key] = clean_target
            else:
                raise ValueError("Only App/Website action targets are editable")
            save_config(self.config, self.config_path)
            current = str(self.profiles.current_key)
            self.reload()
            self.profiles.current_key = current
            self.append_log(f"Updated action target: {action} -> {clean_target}")
            return self.snapshot()

    def update_app(self) -> dict:
        with self.lock:
            root = Path(__file__).resolve().parents[1]
            commands = [
                "git pull --ff-only",
                "npm install --prefix ui",
            ]
            output: list[str] = []
            for command in commands:
                try:
                    result = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=180, shell=True)
                except FileNotFoundError as exc:
                    self.append_log(f"Update failed: could not start command shell for {command}")
                    raise RuntimeError(
                        "Update could not start because Windows could not find a required command runner. "
                        "Try updating from Command Prompt with: git pull && npm install --prefix ui"
                    ) from exc
                if result.stdout.strip():
                    output.append(f"$ {command}\n{result.stdout.strip()}")
                if result.stderr.strip():
                    output.append(f"$ {command} [stderr]\n{result.stderr.strip()}")
                if result.returncode != 0:
                    self.append_log(f"Update failed: {command}")
                    detail = "\n".join(output[-2:]) or f"Command exited with code {result.returncode}"
                    raise RuntimeError("Update failed while running " + command + "\n" + detail)
            self.reload()
            self.append_log("Update complete. Restart SonarDeck Studio if the UI does not refresh automatically.")
            return self.snapshot()


class SonarDeckRequestHandler(BaseHTTPRequestHandler):
    server_version = "SonarDeckModernApi/0.1"

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "content-type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send_json({"ok": True})

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/api/state":
                self._send_json({"ok": True, "state": self.server.state.snapshot()})
            elif parsed.path == "/api/health":
                self._send_json({"ok": True, "service": "sonardeck-modern-api"})
            else:
                self._send_json({"ok": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)
        except Exception as exc:
            self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        length = int(self.headers.get("content-length", "0") or "0")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        payload = json.loads(raw or "{}")
        try:
            if parsed.path == "/api/fire":
                state = self.server.state.fire(str(payload.get("event", "")))
            elif parsed.path == "/api/profile":
                state = self.server.state.set_profile(str(payload.get("profile", "")))
            elif parsed.path == "/api/label":
                state = self.server.state.save_label(str(payload.get("profile", "")), str(payload.get("event", "")), str(payload.get("label", "")))
            elif parsed.path == "/api/icon":
                state = self.server.state.save_icon(
                    str(payload.get("profile", "")),
                    str(payload.get("event", "")),
                    str(payload.get("icon", "")),
                )
            elif parsed.path == "/api/color":
                state = self.server.state.save_color(
                    str(payload.get("profile", "")),
                    str(payload.get("event", "")),
                    str(payload.get("color", "")),
                )
            elif parsed.path == "/api/mapping":
                state = self.server.state.save_mapping(
                    str(payload.get("profile", "")),
                    str(payload.get("event", "")),
                    str(payload.get("action", "")),
                    payload.get("label"),
                )
            elif parsed.path == "/api/app-action":
                state = self.server.state.add_app_action(
                    str(payload.get("key", "")),
                    str(payload.get("label", "")),
                    str(payload.get("command", "")),
                    str(payload.get("profile", "")),
                    str(payload.get("event", "")),
                    str(payload.get("kind", "launch")),
                )
            elif parsed.path == "/api/action-target":
                state = self.server.state.update_action_target(
                    str(payload.get("action", "")),
                    str(payload.get("target", "")),
                )
            elif parsed.path == "/api/update":
                state = self.server.state.update_app()
            else:
                self._send_json({"ok": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)
                return
            self._send_json({"ok": True, "state": state})
        except Exception as exc:
            self._send_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args: object) -> None:
        logging.getLogger("sonardeck.web").debug(format, *args)


class SonarDeckServer(ThreadingHTTPServer):
    state: SonarDeckApiState


def run(host: str = "127.0.0.1", port: int = 8765, config_path: str | None = None) -> None:
    server = SonarDeckServer((host, port), SonarDeckRequestHandler)
    server.state = SonarDeckApiState(config_path)
    print(f"SonarDeck Modern API running on http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="SonarDeck modern UI local API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--config")
    args = parser.parse_args()
    run(args.host, args.port, args.config)


if __name__ == "__main__":
    main()
