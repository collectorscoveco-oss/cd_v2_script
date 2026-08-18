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
- bridge status/log area

## Next steps

1. Add mapping action editing in the React UI.
2. Add create website/app/hotkey action builders.
3. Add profile create/duplicate/rename/reorder/delete.
4. Add live Sonar mixer display through the API.
5. Add serial hardware status through the API.
6. Add Tauri packaging after the UI shape feels right.
