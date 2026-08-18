import json
import tempfile
from pathlib import Path

from bridge.web_api import SonarDeckApiState, action_category


def _temp_config():
    source = json.loads(Path("bridge/config.example.json").read_text())
    handle = tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False)
    json.dump(source, handle)
    handle.close()
    return handle.name


def test_spotify_protocol_is_app_not_website():
    cfg = {"actions": {"app": {"open": {"spotify": "spotify:", "youtube": "https://youtube.com"}}}}
    assert action_category("app.open.spotify", cfg) == "App"
    assert action_category("app.open.youtube", cfg) == "Website"


def test_action_target_can_be_edited():
    path = _temp_config()
    state = SonarDeckApiState(path)
    snap = state.update_action_target("app.open.spotify", "spotify:")
    action = next(item for item in snap["actions"] if item["id"] == "app.open.spotify")
    assert action["category"] == "App"
    assert action["target"] == "spotify:"
    assert action["editableTarget"] is True


def test_app_action_can_create_website_or_protocol_shortcut():
    path = _temp_config()
    state = SonarDeckApiState(path)
    snap = state.add_app_action("spotify_protocol", "Spotify", "spotify:", "sonar", "BTN_03_PRESS", "open")
    button = next(item for item in snap["buttons"] if item["event"] == "BTN_03_PRESS")
    assert button["action"] == "app.open.spotify_protocol"
    assert button["category"] == "App"
