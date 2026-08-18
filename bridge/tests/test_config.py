from bridge.config import load_config


def test_example_config_loads():
    cfg = load_config()
    assert "profiles" in cfg
    assert "sonar" in cfg["profiles"]["items"]
    assert cfg["profiles"]["items"]["sonar"]["events"]["BTN_08_LONG"] == "profile.next"
