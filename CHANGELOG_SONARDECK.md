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
- Added `scripts/run_virtual_deck.bat` and `bridge.virtual_deck`, a GUI virtual controller for testing the final button/profile mappings before Arduino hardware arrives.
- Expanded the virtual controller with live Sonar mixer bars, profile-colored pages, keyboard shortcuts, a button/profile editor, and profile-switch sound controls/test buttons.
- Reworked the virtual deck buttons into polished Stream Deck-style cards with action category colors and an Edit Mapping Mode where clicking a deck button selects it for editing.
- Smoothed virtual deck card hover behavior so cards no longer flash/flicker when moving over nested text.
- Added a top toolbar with Check for Updates, Refresh Sonar, Test Profile Sound, Open Config Folder, and Edit Mapping Mode.
- Removed deck-card hover event bindings entirely to eliminate the remaining Tkinter graphical glitch.
- Added editable button names/labels saved per profile/control.
- Added a GUI app picker so custom apps can be selected and mapped without editing JSON.
- Reduced duplicate default short-press profile-switch mappings; long-press Button 8 remains the dedicated page switch.
- Added more default profiles: Gaming, Streaming, Music, and Desktop.
- Expanded profile-switch audio modes: off, beep, profile-specific beeps, terminal bell, Windows system sound, WAV file, profile-specific WAV files, and Windows voice.
- Updated the virtual controller so button/encoder labels refresh when the active profile/page changes.
- Updated the virtual controller to refresh its Sonar status immediately after any action, plus a delayed second refresh for GG/Sonar API lag.
- Added `scripts/reset_config_to_default.bat` and `docs/plug-and-play.md` so the Windows setup path is closer to plug-and-play.
- Updated `scripts/setup_windows.bat` to create `bridge/config.json` automatically when missing.
- Changed the default V1 `BTN_08_PRESS` mapping to media play/pause so the default config has no unimplemented output-rotation action; `BTN_08_LONG` remains profile/page switch.
