# SonarDeck Studio Modern UI Prototype

This is the first pass at the recommended UI migration: a modern React/TypeScript frontend backed by the existing Python SonarDeck bridge.

## Why this exists

Raw Tkinter is useful for the V1 debug/control app, but it is showing visual limits. The modern UI lets us move toward a professional desktop app without rewriting the working Sonar, hotkey, app-launch, profile, and future Arduino logic.

## Current architecture

- `bridge/web_api.py` — local Python API for state, profile switching, button firing, and display-name saves.
- `ui/` — Vite + React + TypeScript frontend.
- Future packaged app target: Tauri + React/TypeScript using the same Python bridge API.

## Run on Windows

```bat
scripts\run_modern_ui.bat
```

That starts:

- Python bridge API at `http://127.0.0.1:8765`
- React dev UI at `http://127.0.0.1:5173`

## Current prototype features

- polished dark SonarDeck Studio layout
- profile/page pills
- 3x3 virtual deck cards
- click a card to fire its mapped event
- right-click a card to select it for display-name editing
- save button display name back to `bridge/config.json`
- pages/actions/hardware tabs
- 10-button layout support: Button 10 is a wide Play/Pause control; hold Button 10 for Next Page (`BTN_10_LONG`)
- Manual remapping in the Mapping tab: right-click a card, choose an action from the dropdown, then Save Action + Name
- Manual `.exe` app action creation in the Mapping tab: paste a full Windows `.exe` path, add it to the action list, and optionally assign it directly to the selected button
- Direct Windows `.exe` launching for pasted paths, including Spotify paths under `AppData\Roaming\Spotify`
- App/protocol shortcuts like `spotify:` are categorized as App buttons instead of Website buttons, and existing App/Website action targets can be edited from Button Setup
- Simplified Button Setup modes: Use existing action, Open an `.exe`, or Open website/protocol
- Brand/logo icon system for current and future buttons using `simple-icons` plus Lucide fallbacks; see `docs/icons.md`
- Sidebar Check / Install Updates button runs `git pull --ff-only` and `npm install --prefix ui` through the local bridge API
- Vite is pinned to strict port `5173`, and launchers clear old SonarDeck listeners before starting so it does not silently move to `5174`
- Launchers run `npm install` before starting the UI so newly added frontend packages such as `simple-icons` are installed after `git pull`
- Automatic icon matching also checks the configured app path / `.exe` filename, so newly added apps can find a matching brand icon without manual setup
- Button Setup includes a manual Button Icon picker with Auto, brand logos, and generic fallback icons; selected overrides are saved per page/button
- OrcaSlicer is included as a selectable icon and is auto-detected from `OrcaSlicer.exe` / Orca labels
- Spotify defaults use the `spotify:` app protocol instead of assuming `spotify.exe` is on PATH
- Sonar mic mute toggles keep a bridge-side fallback state when GG does not report a mute field, so repeated presses can mute and unmute instead of only muting
- Explicit Sonar actions are available for Mic Mute Toggle, Mic Mute, and Mic Unmute
- Hotkey support covers letters, numbers, F1-F24, arrows, and common keys so Discord/OBS custom hotkeys can be configured more reliably
- Discord Mute default hotkey is now `F13` instead of `Ctrl+Shift+M` because Chrome can steal `Ctrl+Shift+M` and open the profile menu
- Button Setup includes a Button Color picker with Auto Color or a custom per-page/per-button color override

## Next steps

1. Add mapping action editing in the React UI.
2. Add create website/app/hotkey action builders.
3. Add profile create/duplicate/rename/reorder/delete.
4. Add live Sonar mixer display through the API.
5. Add serial hardware status through the API.
6. Add Tauri packaging after the UI shape feels right.
