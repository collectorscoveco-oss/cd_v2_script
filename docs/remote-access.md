# SonarDeck Remote Access

Use this when the tablet, phone, or second PC is not on the same Wi-Fi/LAN subnet as the bridge/server PC.

## What actually works

SonarDeck is a browser app backed by a local bridge. That means a tablet on guest Wi-Fi or a different VLAN cannot reach a plain LAN IP like `http://192.168.1.50:8766` unless you add a path between the networks.

Use one of these instead:

### Option 1: Tailscale

Best for private access.

1. Install Tailscale on the bridge/server PC.
2. Install Tailscale on the tablet/phone/other PC.
3. Sign in to the same account on both devices.
4. Open the Tailscale IP or MagicDNS name for the bridge/server PC.
5. Add the SonarDeck port: `http://<tailscale-ip>:8766`

### Option 2: Cloudflare Tunnel

Best if you want a public HTTPS link.

1. Run Cloudflare Tunnel on the bridge/server PC.
2. Point it at the SonarDeck release launcher port: `8766`.
3. Open the tunnel URL on the tablet/phone.
4. Keep the bridge/server PC running while you use the deck.

### Option 3: Same Wi-Fi/LAN

Simplest if the devices are already on the same subnet.

- Run `scripts\run_release.bat` on the bridge/server PC.
- Open the printed LAN URL on the tablet/phone.
- Do not use `127.0.0.1` on any other device.

## Recommendation

If you want the easiest cross-network setup, use Tailscale first. It is the most reliable replacement for the old “companion app” idea because it keeps the setup web-based and works from any device with a browser.
