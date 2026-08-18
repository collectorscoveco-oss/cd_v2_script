from __future__ import annotations

import argparse
import json

from .actions.sonar import SonarClient
from .config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely test SonarDeck Sonar volume/mute actions")
    parser.add_argument("--channel", default="media", choices=["game", "chat", "media", "aux", "mic"], help="Channel to test")
    parser.add_argument("--delta", type=float, default=0.01, help="Temporary volume delta for the test")
    parser.add_argument("--apply", action="store_true", help="Actually change volume briefly, then restore it")
    args = parser.parse_args()

    config = load_config()
    client = SonarClient(config.get("actions", {}).get("sonar", {}))
    print("api_base:", client.api_base)
    print("mode:", client.get_mode())
    settings = client.get_volume_settings()
    channel_id = client.channels.get(args.channel, args.channel)
    current_volume = client._extract_volume(settings, channel_id)
    current_muted = client._extract_muted(settings, channel_id)
    print(f"channel: {args.channel} -> {channel_id}")
    print("current_volume:", current_volume)
    print("current_muted:", current_muted)

    if current_volume is None:
        print("Could not extract channel volume. Paste this output back.")
        print(json.dumps(settings, indent=2)[:4000])
        return

    if not args.apply:
        print("Read-only test passed. Add --apply to briefly change and restore volume.")
        return

    new_volume = max(0.0, min(1.0, current_volume + args.delta))
    if new_volume == current_volume:
        new_volume = max(0.0, min(1.0, current_volume - args.delta))
    print(f"Setting {args.channel} volume to {new_volume}...")
    client.set_channel_volume(args.channel, new_volume)
    print("Restoring original volume...")
    client.set_channel_volume(args.channel, current_volume)
    print("Volume action test completed and restored.")


if __name__ == "__main__":
    main()
