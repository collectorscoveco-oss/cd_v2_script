import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

from bridge.config import migrate_config
from bridge.web_api import GITHUB_LATEST_RELEASE_URL, SonarDeckApiState, action_category, run


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


def test_discord_mute_hotkey_migrates_away_from_chrome_shortcut_and_f13():
    for old_combo in (["ctrl", "shift", "m"], ["f13"]):
        cfg = {"actions": {"hotkey": {"discord_mute": old_combo}}}
        assert migrate_config(cfg) is True
        assert cfg["actions"]["hotkey"]["discord_mute"] == ["ctrl", "alt", "shift", "m"]


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


def test_button_icon_override_can_be_saved_and_cleared():
    path = _temp_config()
    state = SonarDeckApiState(path)
    snap = state.save_icon("sonar", "BTN_03_PRESS", "spotify")
    button = next(item for item in snap["buttons"] if item["event"] == "BTN_03_PRESS")
    assert button["icon"] == "spotify"

    snap = state.save_icon("sonar", "BTN_03_PRESS", "")
    button = next(item for item in snap["buttons"] if item["event"] == "BTN_03_PRESS")
    assert button["icon"] == ""


def test_button_color_override_can_be_saved_and_cleared():
    path = _temp_config()
    state = SonarDeckApiState(path)
    snap = state.save_color("sonar", "BTN_03_PRESS", "#ff00aa")
    button = next(item for item in snap["buttons"] if item["event"] == "BTN_03_PRESS")
    assert button["color"] == "#ff00aa"
    assert button["customColor"] == "#ff00aa"

    snap = state.save_color("sonar", "BTN_03_PRESS", "")
    button = next(item for item in snap["buttons"] if item["event"] == "BTN_03_PRESS")
    assert button["customColor"] == ""
    assert button["color"] == button["autoColor"]


def test_hotkey_action_can_be_created_and_assigned():
    path = _temp_config()
    state = SonarDeckApiState(path)
    snap = state.add_hotkey_action("discord_mute_alt", "Discord Mute", "ctrl+alt+shift+m", "apps", "BTN_06_PRESS")
    action = next(item for item in snap["actions"] if item["id"] == "hotkey.discord_mute_alt")
    button = next(item for item in snap["buttons"] if item["event"] == "BTN_06_PRESS")
    assert action["target"] == "ctrl+alt+shift+m"
    assert action["editableTarget"] is True
    assert button["action"] == "hotkey.discord_mute_alt"


def test_hotkey_action_target_can_be_edited():
    path = _temp_config()
    state = SonarDeckApiState(path)
    snap = state.update_action_target("hotkey.discord_mute", "ctrl+alt+shift+m")
    action = next(item for item in snap["actions"] if item["id"] == "hotkey.discord_mute")
    assert action["target"] == "ctrl+alt+shift+m"

def test_fire_reports_success_for_working_action():
    path = _temp_config()
    state = SonarDeckApiState(path)
    calls = []

    class FakeRegistry:
        def execute(self, action):
            calls.append(action)

    state.registry = FakeRegistry()
    snap = state.fire("BTN_10_PRESS")
    assert calls == ["media.play_pause"]
    assert snap["lastAction"]["ok"] is True
    assert "media.play_pause" in snap["lastAction"]["message"]


def test_fire_reports_action_errors_in_state_instead_of_silent_success():
    path = _temp_config()
    state = SonarDeckApiState(path)

    class FailingRegistry:
        def execute(self, action):
            raise RuntimeError("synthetic action failure")

    state.registry = FailingRegistry()
    snap = state.fire("BTN_10_PRESS")
    assert snap["lastAction"]["ok"] is False
    assert snap["lastAction"]["action"] == "media.play_pause"
    assert "synthetic action failure" in snap["lastAction"]["message"]
    assert any("ERROR" in entry and "synthetic action failure" in entry for entry in snap["log"])


def test_run_defaults_to_lan_binding(monkeypatch):
    seen = {}

    class FakeServer:
        def __init__(self, address, handler):
            seen["address"] = address
            seen["handler"] = handler
            self.state = None
            self.static_dir = None

        def __setattr__(self, name, value):
            if name == "static_dir":
                seen[name] = value
            object.__setattr__(self, name, value)

        def serve_forever(self):
            seen["served"] = True

    monkeypatch.setattr("bridge.web_api.SonarDeckServer", FakeServer)
    monkeypatch.setattr("bridge.web_api.SonarDeckApiState", lambda config_path=None: {"config_path": config_path})

    run()

    assert seen["address"] == ("0.0.0.0", 8765)
    assert seen["served"] is True
    expected_static_dir = Path("ui/dist").resolve() if Path("ui/dist").is_dir() else None
    assert seen["static_dir"] == expected_static_dir


def test_run_accepts_explicit_static_dir(monkeypatch, tmp_path):
    seen = {}
    static_dir = tmp_path / "ui" / "dist"
    static_dir.mkdir(parents=True)
    (static_dir / "index.html").write_text("<html></html>")

    class FakeServer:
        def __init__(self, address, handler):
            seen["address"] = address
            seen["handler"] = handler
            self.state = None
            self.static_dir = None

        def __setattr__(self, name, value):
            if name == "static_dir":
                seen[name] = value
            object.__setattr__(self, name, value)

        def serve_forever(self):
            seen["served"] = True

    monkeypatch.setattr("bridge.web_api.SonarDeckServer", FakeServer)
    monkeypatch.setattr("bridge.web_api.SonarDeckApiState", lambda config_path=None: {"config_path": config_path})

    run(static_dir=str(static_dir))

    assert seen["address"] == ("0.0.0.0", 8765)
    assert seen["served"] is True
    assert str(seen["static_dir"]).endswith("ui/dist")


def test_run_diagnostics_reports_missing_sonar_api_base():
    path = _temp_config()
    state = SonarDeckApiState(path)
    assert state.registry.ctx.sonar_client is not None
    state.registry.ctx.sonar_client.api_base = None
    snap = state.run_diagnostics()
    diagnostics = snap["diagnostics"]
    assert any("not discovered" in line for line in diagnostics["summary"])
    assert diagnostics["probe"] == []


def test_update_app_runs_git_flow_inside_checkout(monkeypatch, tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / ".git").mkdir()
    calls = []

    def fake_run(command, cwd, text, capture_output, timeout, shell):
        calls.append((command, cwd, shell))
        return SimpleNamespace(stdout=f"{command} ok", stderr="", returncode=0)

    monkeypatch.setattr("bridge.web_api.repo_root", lambda: root)
    monkeypatch.setattr("bridge.web_api.subprocess.run", fake_run)
    state = SonarDeckApiState(_temp_config())

    result = state.update_app()

    assert result["mode"] == "git"
    assert result["snapshot"]["lastAction"]["ok"] is True
    assert calls == [
        ("git pull --ff-only", root, True),
        ("npm install --prefix ui", root, True),
    ]


def test_update_app_falls_back_to_release_url_outside_checkout(monkeypatch, tmp_path):
    root = tmp_path / "release"
    root.mkdir()

    def fail_run(*args, **kwargs):
        raise AssertionError("subprocess.run should not be called in release mode")

    monkeypatch.setattr("bridge.web_api.repo_root", lambda: root)
    monkeypatch.setattr("bridge.web_api.subprocess.run", fail_run)
    state = SonarDeckApiState(_temp_config())

    result = state.update_app()

    assert result["mode"] == "release"
    assert result["update_url"] == GITHUB_LATEST_RELEASE_URL
    assert "Download the latest ZIP" in result["message"]
    assert "scripts/run_release.bat" in result["message"]
    assert result["snapshot"]["lastAction"]["ok"] is True

