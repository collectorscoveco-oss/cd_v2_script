from bridge.profiles import ProfileManager


def test_profile_switch_and_event_mapping():
    cfg = {
        "default": "one",
        "switch_sound": {"enabled": False},
        "items": {
            "one": {"name": "One", "events": {"BTN_01_PRESS": "a.one", "BTN_08_LONG": "profile.next"}},
            "two": {"name": "Two", "events": {"BTN_01_PRESS": "a.two"}},
        },
    }
    pm = ProfileManager(cfg)
    assert pm.current_name == "One"
    assert pm.action_for_event("BTN_01_PRESS") == "a.one"
    pm.next_profile()
    assert pm.current_name == "Two"
    assert pm.action_for_event("BTN_01_PRESS") == "a.two"
