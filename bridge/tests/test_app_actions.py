from bridge.actions.app import _looks_like_protocol, _strip_wrapping_quotes


def test_strip_wrapping_quotes():
    assert _strip_wrapping_quotes('"C:\\Users\\crsma\\AppData\\Roaming\\Spotify\\Spotify.exe"') == 'C:\\Users\\crsma\\AppData\\Roaming\\Spotify\\Spotify.exe'
    assert _strip_wrapping_quotes(' spotify: ') == 'spotify:'


def test_protocol_detection():
    assert _looks_like_protocol('spotify:')
    assert _looks_like_protocol('https://open.spotify.com')
    assert not _looks_like_protocol('C:\\Users\\crsma\\AppData\\Roaming\\Spotify\\Spotify.exe')
