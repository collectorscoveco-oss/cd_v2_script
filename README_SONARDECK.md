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
copy bridge\config.example.json bridge\config.json
scripts\run_bridge.bat
```

## Sonar probe

With SteelSeries GG/Sonar running:

```bat
scripts\sonar_probe.bat
```

If the probe fails, paste the output back. SteelSeries GG's local API endpoints can change by version, so the Sonar module is intentionally isolated for fast adjustment.

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
