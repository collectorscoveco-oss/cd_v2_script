# SonarDeck Studio

A touch-friendly web Stream Deck for phone, tablet, and desktop.

## Download

For the easiest public-use install, download the latest GitHub Release Windows installer and double-click the NSIS `.exe` setup file.

Use the MSI only if you specifically need it for managed installation.

After install, launch SonarDeck Studio from the Start menu. The installed app includes the built web UI and the Python bridge, so users do not need to build the frontend first. It opens the LAN URL on port 8766 and may ask Windows Firewall for permission the first time. Run the app on the bridge/server PC; a separate gaming PC, tablet, or phone can connect to that bridge URL from the UI. In the UI, the connection field is the bridge/server URL, so point it at the local bridge PC, a Cloudflare tunnel URL, or another PC on the network. From a different device, use the bridge PC's LAN IP or tunnel URL; do not use 127.0.0.1.

The Update button is split for both install types: dev checkouts keep using `git pull --ff-only` plus `npm install --prefix ui`, while installed users go back to the latest GitHub release page to download the newer installer and rerun it.

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

If you are working from the repo instead of the installed desktop app:

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
