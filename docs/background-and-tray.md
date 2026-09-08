# Running SonarDeck in the Background

During development, the normal launcher keeps command windows open:

```bat
scripts\run_modern_ui.bat
```

That is useful when something is broken because the errors stay visible.

For day-to-day use, use the background launcher:

```bat
scripts\run_modern_ui_background.bat
```

This starts the Python API and React UI hidden, writes logs under `logs\`, and opens the browser at:

```text
http://127.0.0.1:5173
```

The same launcher binds the bridge and dev server to `0.0.0.0`, so a phone/tablet on the same LAN can open `http://<pc-ip>:5173` and still reach the bridge.

Use this only on a trusted LAN; the bridge is currently unauthenticated.

To stop the hidden background processes:

```bat
scripts\stop_modern_ui.bat
```

## First run

If UI dependencies are not installed yet, the background launcher opens an `npm install` setup window. Let that finish, then run the background launcher again.

## Troubleshooting

If the background launcher does not open the browser or the page does not load, use the visible launcher instead:

```bat
scripts\run_modern_ui.bat
```

It keeps the API/UI windows open so you can see errors.

Logs for background mode:

```text
logs\sonardeck-api.log
logs\sonardeck-ui.log
```

## Tray app direction

The background launcher is not a real system tray app yet. It is the practical V1 answer so command windows do not stay visible.

A real tray app should come with packaging:

- Tauri desktop shell
- tray menu: Open Studio, Check Updates, Restart Bridge, Quit
- starts the Python bridge as a child/background process
- no browser tab required unless the user chooses web mode
