# SonarDeck Changelog

## Unreleased

- Added no-screen SonarDeck V1 Arduino firmware.
- Added short/long press behavior for Button 8.
- Added Python bridge package with profile/page support.
- Added customizable profile switch sounds: beep, sound file, or terminal bell.
- Added modular action registry for Windows media, app launching, hotkeys, and Sonar.
- Added Sonar probe helper for live Windows testing.
- Added Sonar control parser/apply test helper for safe volume testing.
- Updated Sonar API discovery to use the Sonar subapp `webServerAddress` from SteelSeries Engine `/subApps`.
- Updated volume/mute extraction for nested `/volumeSettings/classic` and streamer shapes.
- Added Windows setup/run scripts and V1 docs.
- Added `scripts/simulate_event.bat` for testing mapped actions without Arduino hardware.
- Changed the default V1 `BTN_08_PRESS` mapping to media play/pause so the default config has no unimplemented output-rotation action; `BTN_08_LONG` remains profile/page switch.
