from __future__ import annotations

import json
from .config import load_config
from .actions.sonar import SonarClient


def main() -> None:
    config = load_config()
    client = SonarClient(config.get("actions", {}).get("sonar", {}))
    print("api_base:", client.api_base)
    if not client.api_base:
        print("SteelSeries GG API base was not discovered. Make sure GG/Sonar is running.")
        return
    try:
        settings = client.get_volume_settings()
        print(json.dumps(settings, indent=2))
    except Exception as exc:
        print("Probe failed:", exc)
        print("If this fails, paste this output back so we can adjust endpoints for your GG/Sonar version.")


if __name__ == "__main__":
    main()
