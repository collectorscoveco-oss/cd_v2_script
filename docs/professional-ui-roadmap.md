# SonarDeck Professional UI Roadmap

The Virtual Controller is intentionally evolving from a test utility into a real companion app. The direction should feel closer to Linear/Raycast/SteelSeries than a raw Tkinter form.

## Design direction

- Dark, low-glare gaming/workstation UI.
- Clean cards instead of plain default buttons.
- Clear hierarchy: deck first, editing second, logs last.
- Obvious page/profile identity through accent color and sound.
- stable no-flicker controls: deck cards do not change color on hover and normal clicks avoid full deck redraws
- explicit button display-name controls: Save Name Only and Clear Custom Name
- Fewer giant dropdowns; prefer filtered choices and small builders.

## Next polish passes

1. **Tabbed right panel**
   - Mapping
   - Actions
   - Profiles
   - Settings
   - Hardware

2. **Button card metadata**
   - custom display name
   - optional emoji/icon
   - action category color
   - short/long press indicator

3. **Hardware readiness/status tab**
   - Arduino connected/not connected
   - selected serial port
   - firmware version when available
   - last serial event received
   - quick button test mode

4. **First-run setup wizard**
   - check Python dependencies
   - check Git/GitHub update path
   - check SteelSeries GG/Sonar API
   - create config if missing
   - offer default profile set

5. **Packaged app feel**
   - Desktop shortcut
   - app icon
   - version number in the title/about dialog
   - launch without showing Command Prompt where possible

6. **Safer customization**
   - backup before major changes
   - restore config backup
   - reset current page only
   - duplicate profile before editing

## Current implemented pieces

- Virtual deck cards
- no hover color changes
- editable button names
- custom app picker
- custom website builder
- custom hotkey builder
- action type filtering
- profile create/duplicate/rename
- backup/restore
- check/install updates
- profile switch sounds
- live Sonar mixer display
