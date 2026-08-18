# SonarDeck Plug-and-Play Quick Start

Goal: get the software ready now, then plug in the Arduino later and use the same Sonar mappings.

## Right now, before the Arduino arrives

1. Install GitHub CLI / Git if needed.
2. Clone or pull this branch on the gaming PC.
3. Open SteelSeries GG and make sure Sonar is enabled.
4. Run setup:

```bat
scripts\setup_windows.bat
```

5. Run the virtual controller:

```bat
scripts\run_virtual_deck.bat
```

The virtual controller is the GUI test deck. It lets you click the same mapped events the Arduino will send later. It also includes:

- live Sonar mixer bars for Game/Chat/Media/Mic
- profile-colored pages
- editable button/control mappings saved to `bridge\config.json`
- F1-F9 and Ctrl+Alt+1..9 shortcuts while the window is focused
- profile-switch audio modes: `off`, `beep`, `profile_beeps`, `terminal_bell`, `system`, `file`, `profile_files`, `voice`
- a Test Current sound button and WAV picker

## If your config is old

If you previously tested older versions of this branch, reset your local config once:

```bat
scripts\reset_config_to_default.bat
```

That copies `bridge\config.example.json` to `bridge\config.json`.

## Button mapping, V1

```text
BTN_01_PRESS  Game volume up
BTN_02_PRESS  Game volume down
BTN_03_PRESS  Chat volume up
BTN_04_PRESS  Chat volume down
BTN_05_PRESS  Media volume up
BTN_06_PRESS  Media volume down
BTN_07_PRESS  Mic mute toggle
BTN_08_PRESS  Play / pause
BTN_08_LONG   Switch profile/page
BTN_09_PRESS  Windows mute
ENC_01_CW     Windows volume up
ENC_01_CCW    Windows volume down
ENC_01_PRESS  Windows mute
```

## When the Arduino arrives

1. Open the Arduino IDE.
2. Flash:

```text
firmware/sonardeck_v1/sonardeck_v1.ino
```

3. Wire one button first and confirm it sends a serial event.
4. Run the hardware bridge:

```bat
scripts\run_bridge.bat
```

5. Press the physical button. The bridge should log the event and run the same mapped action you tested in the GUI.

## Troubleshooting order

Use this order so each layer is proven before moving on:

```text
SteelSeries GG/Sonar open
  ↓
scripts\sonar_probe.bat
  ↓
scripts\sonar_control_test.bat --apply
  ↓
scripts\run_virtual_deck.bat
  ↓
Arduino Serial Monitor event
  ↓
scripts\run_bridge.bat
```
