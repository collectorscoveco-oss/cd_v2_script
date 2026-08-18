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
    print("Trying known Sonar/GG endpoints...")
    results = client.probe()
    for item in results:
        status = "OK" if item.get("ok") else "FAIL"
        print(f"[{status}] {item.get('base')}{item.get('endpoint')}")
        if item.get("ok"):
            data = item.get("data")
            if isinstance(data, (dict, list)):
                print(json.dumps(data, indent=2)[:4000])
            else:
                print(str(data)[:1000])
        else:
            print("  ", item.get("error"))
    if not any(item.get("ok") for item in results):
        print("No endpoints responded. Paste this full output back so we can adjust for your GG/Sonar version.")


if __name__ == "__main__":
    main()
