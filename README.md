# SonarDeck Studio

A touch-friendly web Stream Deck for phone, tablet, and desktop.

## Download

For the easiest public-use install, download the latest GitHub Release ZIP, extract it, and run:

```bat
scripts\run_release.bat
```

That package includes the built web UI and the Python bridge, so users do not need to build the frontend first. The release launcher opens the LAN URL on port 8766 and may ask Windows Firewall for permission the first time. Run the package on the bridge/server PC; a separate gaming PC, tablet, or phone can connect to that bridge URL from the UI.

## What it does

- Big touch-friendly deck buttons
- Editor mode for remapping buttons
- Deck mode for button-only fullscreen use
- PC companion bridge for local control
- LAN-friendly connection settings
- Profiles/pages and hotkeys

## Requirements

- Windows PC
- Python 3.11+ for the release package
- Node.js LTS only if you want to run the developer UI

## Developer run

If you are working from the repo instead of a release ZIP:

```bat
scripts\run_modern_ui.bat
```

That starts the Python bridge and the Vite dev UI.

## Project layout

- `bridge/` — Python bridge and action handling
- `ui/` — React/TypeScript front end
- `scripts/` — Windows launchers
- `docs/` — notes and UI direction

## Notes

- The release package is the recommended public download.
- The bridge is trusted-LAN only right now; do not expose it publicly.
- If you change mappings in the editor, use the save buttons so changes persist to the config file.
