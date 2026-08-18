from pathlib import Path

from bridge.config import load_config


def test_example_config_loads():
    cfg = load_config(Path(__file__).resolve().parents[1] / "config.example.json")
    assert "profiles" in cfg
    assert "sonar" in cfg["profiles"]["items"]
    events = cfg["profiles"]["items"]["sonar"]["events"]
    assert events["BTN_10_PRESS"] == "media.play_pause"
    assert events["BTN_10_LONG"] == "profile.next"
    assert "BTN_08_LONG" not in events
