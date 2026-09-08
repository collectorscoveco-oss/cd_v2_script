# SonarDeck Studio

A touch-friendly web Stream Deck for phone, tablet, and desktop.

## Start here

Read the short guide first:

- [Quick Start](docs/quick-start.md)

## What you need to know

- **Bridge/server PC** = the Windows PC that runs `scripts\run_release.bat`
- **Control device** = phone, tablet, or second PC that opens the bridge URL
- If you only have one PC, use that same PC for both

## Public download

1. Download the latest GitHub Release ZIP.
2. Extract it on the bridge/server PC.
3. Run `scripts\run_release.bat`.
4. Use the local URL on that PC, or the LAN/tunnel URL on another device.
   - Other devices must be on the same Wi-Fi/LAN subnet, or they need a tunnel.

The Update button is split for both install types: dev checkouts keep using `git pull --ff-only` plus `npm install --prefix ui`, while release ZIPs open the latest GitHub release page so you can download the newer ZIP and rerun `scripts\run_release.bat`.

## What it does

- Big touch-friendly deck buttons
- Editor mode for remapping buttons
- Deck mode for button-only fullscreen use
- PC bridge for local control
- LAN-friendly connection settings
- Profiles/pages and hotkeys

## Developer run

If you are working from the repo instead of the release ZIP:

```bat
scripts\run_modern_ui.bat
```

That starts the Python bridge and the Vite dev UI.

## Project layout

- `bridge/` — Python bridge and action handling
- `ui/` — React/TypeScript front end
- `scripts/` — Windows launchers
- `docs/` — quick start and reference notes

## Notes

- The release ZIP is the recommended public download.
- The bridge is trusted-LAN only right now; do not expose it publicly.
- If you change mappings in the editor, use the save buttons so changes persist to the config file.
