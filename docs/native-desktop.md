# SonarDeck Native Desktop App

Option 1 is the active direction: **Tauri + React/TypeScript**, keeping the existing Python bridge.

Option 2, saved for later if Tauri does not work out well: **C# / .NET WPF or WinUI**.

## Why Tauri first

Tauri lets SonarDeck keep the current React UI while running inside a native Windows app window instead of Chrome. This should reduce browser-specific problems such as Chrome stealing hotkeys and removes the need for the user to think about `5173` once packaged.

## Current desktop development launcher

From the project root on Windows:

```bat
scripts\run_desktop_app.bat
```

This launcher:

1. Verifies Node/npm is installed.
2. Verifies Rust/Cargo is installed.
3. Verifies Python is installed.
4. Creates `bridge\config.json` if missing.
5. Runs `npm install` in `ui`.
6. Stops old listeners on `8765` and `5173`.
7. Starts the Python bridge API on `0.0.0.0:8765`.
8. Starts the Tauri native desktop window.

Use this only on a trusted LAN; the bridge is currently unauthenticated. On another device, open the bridge/server LAN URL printed by the launcher, not `127.0.0.1`.

The public release path is the ZIP plus `scripts\run_release.bat`. The Tauri shell package is still future work and is not the recommended public install path yet.

## First-time Rust requirement

Tauri needs Rust. Install it from:

```text
https://rustup.rs
```

After installing Rust, open a **new** Command Prompt so `cargo` is on PATH, then rerun:

```bat
scripts\run_desktop_app.bat
```

## What stays the same

The existing Python bridge remains responsible for:

- SteelSeries Sonar API control
- profiles/pages
- Arduino/serial events
- hotkeys
- app launches
- config saving
- icon/color/mapping API

The existing browser launcher remains as a fallback:

```bat
scripts\run_modern_ui.bat
```

## GitHub packages/releases

GitHub packaging is configured in:

```text
.github/workflows/sonardeck-desktop-package.yml
```

It can be run manually from GitHub Actions or automatically by pushing a tag like:

```text
sonardeck-v0.1.0
```

Public users should download the release ZIP, extract it, and run `scripts\run_release.bat`. That is the simple public install path today. The Tauri shell package remains a separate future path.

## Contributors

See:

```text
CONTRIBUTORS.md
```
