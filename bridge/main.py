from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path

from .actions.registry import ActionContext, ActionRegistry
from .config import load_config
from .profiles import ProfileManager
from .serial_device import SerialSettings, read_events


def setup_logging(config: dict) -> None:
    log_cfg = config.get("logging", {})
    level = getattr(logging, str(log_cfg.get("level", "INFO")).upper(), logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_cfg.get("file"):
        path = Path(__file__).resolve().parent / log_cfg["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(path, encoding="utf-8"))
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s", handlers=handlers)


def run(config_path: str | None = None, dry_event: list[str] | None = None) -> None:
    config = load_config(config_path)
    setup_logging(config)
    log = logging.getLogger("sonardeck")
    profiles = ProfileManager(config["profiles"])
    registry = ActionRegistry(ActionContext(config=config, profile_manager=profiles))
    log.info("SonarDeck bridge started. Active profile: %s", profiles.current_name)

    if dry_event:
        for event in dry_event:
            handle_event(event, profiles, registry)
        return

    serial_cfg = config.get("serial", {})
    settings = SerialSettings(
        port=serial_cfg.get("port", "auto"),
        baudrate=int(serial_cfg.get("baudrate", 9600)),
        reconnect_seconds=float(serial_cfg.get("reconnect_seconds", 2)),
    )
    while True:
        try:
            for event in read_events(settings):
                handle_event(event, profiles, registry)
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            log.error("Bridge error: %s. Reconnecting in %.1fs", exc, settings.reconnect_seconds)
            time.sleep(settings.reconnect_seconds)


def handle_event(event: str, profiles: ProfileManager, registry: ActionRegistry) -> None:
    log = logging.getLogger("sonardeck")
    if event == "SONARDECK_READY":
        log.info("Controller ready")
        return
    action = profiles.action_for_event(event)
    if not action:
        log.warning("No action mapped for event %s in profile %s", event, profiles.current_name)
        return
    log.info("%s [%s] -> %s", event, profiles.current_name, action)
    try:
        registry.execute(action)
    except Exception as exc:
        log.error("Action failed for %s -> %s: %s", event, action, exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="SonarDeck V1 bridge")
    parser.add_argument("--config", help="Path to config.json")
    parser.add_argument("--dry-event", action="append", help="Run one or more fake events then exit")
    args = parser.parse_args()
    run(args.config, args.dry_event)


if __name__ == "__main__":
    main()
