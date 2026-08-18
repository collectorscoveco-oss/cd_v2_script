# SonarDeck V1

This branch turns the free Console Deck V2 project into a no-screen SonarDeck prototype.

## V1 decisions

- Use Console Deck V2 as the physical base.
- No OLED/display for V1.
- Arduino sends generic serial events only.
- Windows bridge decides what each button/encoder event does.
- `BTN_08_PRESS` can be a normal action.
- `BTN_10_PRESS` is the dedicated play/pause button.
- `BTN_10_LONG` switches profile/page.
- Profile switch sound is configurable in `bridge/config.json`.

## Firmware events

- `BTN_01_PRESS` ... `BTN_10_PRESS`
- `BTN_10_LONG`
- `ENC_01_CW`
- `ENC_01_CCW`
- `ENC_01_PRESS`
- `SONARDECK_READY` on boot

## First Windows setup

```bat
scripts\setup_windows.bat
```

Before the Arduino arrives, use the GUI virtual controller:

```bat
scripts\run_virtual_deck.bat
```

When the Arduino arrives and is flashed/wired, run the hardware bridge:

```bat
scripts\run_bridge.bat
```

If you already had an older `bridge\config.json`, reset it after pulling new defaults:

```bat
scripts\reset_config_to_default.bat
```

## Test mapped events without Arduino

The best hardware-free test is the GUI virtual deck:

```bat
scripts\run_virtual_deck.bat
```

You can also simulate one event from Command Prompt:

```bat
scripts\simulate_event.bat BTN_05_PRESS
scripts\simulate_event.bat BTN_10_LONG
```

`BTN_05_PRESS` should raise Sonar media volume. `BTN_10_PRESS` should play/pause media. `BTN_10_LONG` should switch profile/page and play the configured beep/sound.

Full plug-and-play notes: `docs\plug-and-play.md`.

## Custom profile/page sound

Edit `bridge/config.json`:

```json
"switch_sound": {
  "enabled": true,
  "mode": "beep",
  "beep_frequency": 880,
  "beep_duration_ms": 90,
  "file": ""
}
```

Modes:

- `beep` - Windows beep frequency/duration.
- `file` - play a `.wav` file from the configured `file` path.
- `terminal_bell` - simple console bell.

## Sonar testing

Run this first on the Windows machine with SteelSeries GG/Sonar open:

```bat
scripts\sonar_probe.bat
```

A good probe shows `api_base: http://127.0.0.1:<sonar-port>` and `[OK]` for `/mode` plus `/volumeSettings/classic` or `/volumeSettings/streamer`.

Then run the read-only control parser test:

```bat
scripts\sonar_control_test.bat
```

If that prints the current media volume/mute state, optionally run a safe apply test that changes media volume briefly and restores it:

```bat
scripts\sonar_control_test.bat --apply
```

Paste the output back if it cannot find or read Sonar. SteelSeries GG endpoints can change, so the Sonar module is isolated for quick fixes.
