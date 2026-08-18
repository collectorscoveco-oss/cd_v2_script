# SonarDeck V1 fork notes

This fork keeps the original ConsoleDeck V2 files and adds a cleaner no-screen SonarDeck V1 prototype.

## What changed

- Added `firmware/sonardeck_v1/sonardeck_v1.ino`
  - No OLED/display required.
  - Emits clear serial events like `BTN_01_PRESS`, `BTN_08_LONG`, `ENC_01_CW`.
  - Button 8 long press is reserved for profile/page switching.
- Added `bridge/`
  - Modular Python bridge.
  - JSON-configurable profiles/pages.
  - Customizable profile switch sounds.
  - Windows media/app/hotkey actions.
  - Initial SteelSeries Sonar client/probe layer.
- Added `scripts/`
  - `setup_windows.bat`
  - `run_bridge.bat`
  - `sonar_probe.bat`
- Added `docs/sonardeck-v1.md`.

## First setup on Windows

```bat
scripts\setup_windows.bat
```

Before the Arduino arrives, use the GUI virtual controller:

```bat
scripts\run_virtual_deck.bat
```

The virtual controller now includes live Sonar mixer bars, profile-colored pages, polished Stream Deck-style button cards with no hover color changes and reduced click-time redraws, a top toolbar with Check / Install Updates, an Edit Mapping Mode where clicking a deck button selects it for editing, editable button display names with dedicated save/clear controls, an Action Type filter, GUI builders for custom app/website/hotkey buttons, a custom app `.exe` finder, profile/page create/duplicate/rename tools, config backup/restore, F1-F9/Ctrl+Alt shortcuts, and profile-switch audio modes (`off`, `beep`, `profile_beeps`, `terminal_bell`, `system`, `file`, `profile_files`, `voice`).

When the Arduino arrives and is flashed/wired, run the hardware bridge:

```bat
scripts\run_bridge.bat
```

If you already had an older `bridge\config.json`, reset it after pulling new defaults:

```bat
scripts\reset_config_to_default.bat
```

You can also test one mapped event from Command Prompt:

```bat
scripts\simulate_event.bat BTN_05_PRESS
scripts\simulate_event.bat BTN_08_LONG
```

Full plug-and-play notes: `docs\plug-and-play.md`.

## Sonar probe

With SteelSeries GG/Sonar running:

```bat
scripts\sonar_probe.bat
```

A good probe shows `api_base: http://127.0.0.1:<sonar-port>` and `[OK]` for `/mode` plus `/volumeSettings/classic` or `/volumeSettings/streamer`.

Then run the read-only parser test:

```bat
scripts\sonar_control_test.bat
```

Optional safe apply test, which changes the media channel volume briefly and restores it:

```bat
scripts\sonar_control_test.bat --apply
```

If the probe or control test fails, paste the output back. SteelSeries GG's local API endpoints can change by version, so the Sonar module is intentionally isolated for fast adjustment.

## Profile switching

Current design:

- Single press = normal mapped action.
- Long press `Button 8` = switch profile/page.
- Profile/page switch can make a sound.

Config example:

```json
"switch_sound": {
  "enabled": true,
  "mode": "beep",
  "beep_frequency": 880,
  "beep_duration_ms": 90,
  "file": ""
}
```

Sound modes:

- `beep`
- `file` for custom `.wav`
- `terminal_bell`
