from typing import Any

from bridge.actions.sonar import SonarClient


class FakeSonarClient(SonarClient):
    def __init__(self):
        super().__init__({"api_base": "http://127.0.0.1:1", "channels": {"mic": "chatCapture"}})
        self.mode = "classic"
        self.settings: dict[str, Any] = {"devices": {"chatCapture": {"volume": 1.0}}}
        self.requests = []

    def get_mode(self):
        return self.mode

    def get_volume_settings(self):
        return self.settings

    def request(self, method, path, payload=None):
        self.requests.append((method, path, payload))
        return {"ok": True}


def test_toggle_mute_uses_cache_when_state_has_no_muted_field():
    client = FakeSonarClient()
    client.toggle_mute("mic")
    client.toggle_mute("mic")
    assert client.requests[0][1] == "/volumeSettings/classic/chatCapture/Mute/true"
    assert client.requests[1][1] == "/volumeSettings/classic/chatCapture/Mute/false"


def test_toggle_mute_uses_reported_muted_state_when_available():
    client = FakeSonarClient()
    client.settings = {"devices": {"chatCapture": {"muted": True}}}
    client.toggle_mute("mic")
    assert client.requests[0][1] == "/volumeSettings/classic/chatCapture/Mute/false"


def test_toggle_mute_prefers_cache_after_success_even_if_reported_state_is_stale():
    client = FakeSonarClient()
    client.settings = {"devices": {"chatCapture": {"muted": False}}}
    client.toggle_mute("mic")
    client.toggle_mute("mic")
    assert client.requests[0][1] == "/volumeSettings/classic/chatCapture/Mute/true"
    assert client.requests[1][1] == "/volumeSettings/classic/chatCapture/Mute/false"


def test_streamer_mute_tries_monitoring_path_first():
    client = FakeSonarClient()
    client.mode = "streamer"
    client.toggle_mute("mic")
    assert client.requests[0][1] == "/volumeSettings/streamer/monitoring/chatCapture/Mute/true"
