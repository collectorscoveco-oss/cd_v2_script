# SonarDeck Icon Direction

The modern UI now uses a mixed icon system:

- real brand SVG logos from `simple-icons` for known apps/services
- Automatic fuzzy brand lookup from the action id, button label, category, configured target, and pasted `.exe` filename
- Manual per-button icon override from Button Setup, with Auto mode to go back to inferred icons
- Lucide fallback icons for generic actions such as media keys, volume, mute, mic, hotkeys, pages, and websites

## Current brand/logo coverage

The registry currently recognizes these by action id, label, or category text:

- Spotify
- Discord
- SteelSeries / GG / Sonar
- YouTube
- OBS Studio
- Bambu Lab / Bambu Studio
- Twitch
- Steam
- Epic Games
- PlayStation
- NVIDIA
- GitHub
- Google Chrome
- VLC media player
- Plex
- Elgato / Stream Deck

## Current generic icon coverage

- Play/Pause
- Previous track
- Next track
- Volume
- Mute
- Microphone
- Hotkey / keyboard shortcut
- Profile/page switching
- Website
- Game/gaming
- Settings/hardware
- Generic app
- Automation/future macro actions
- Video/future streaming actions
- Audio/future music actions
- Output/future device routing actions

## Implementation

Frontend icon logic lives in:

```text
ui/src/actionIcons.tsx
```

It infers icons from:

```text
action id
button label
action category
```

This means new buttons can get useful icons before dedicated icon editing exists.

## Next improvement

Add a real Icon Picker to Button Setup:

```text
Auto icon
Spotify
Discord
SteelSeries
YouTube
OBS
Bambu
Steam
Twitch
Custom SVG/PNG
```

Then store the selected icon override in `bridge/config.json` per button/action.
