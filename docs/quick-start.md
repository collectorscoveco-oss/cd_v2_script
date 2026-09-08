# SonarDeck Studio Quick Start

## Which PC runs what?

- **Bridge/server PC**: the Windows PC that runs `scripts\run_release.bat`
- **Control device**: the phone, tablet, or second PC that opens the bridge URL
- **If you only have one PC**, that same PC is both the bridge/server and the control device

## Easiest setup

1. Download the latest GitHub Release ZIP.
2. Extract it on the **bridge/server PC**.
3. Run `scripts\run_release.bat`.
4. Keep the window open.
5. On the same PC, use the local URL it prints.
6. On another device, open the **bridge/server LAN IP or tunnel URL** it prints.

## What to use on another device

- **Do not** use `127.0.0.1` on your phone or tablet.
- Use the bridge/server PC's printed LAN URL, such as `http://10.0.0.142:8766`
- Your tablet/phone must be on the same Wi-Fi/LAN subnet, not guest Wi-Fi
- If you use a tunnel, open the tunnel URL instead

## If something is confusing

- Start with the same PC first
- Confirm the deck opens locally
- Then try the phone/tablet second

