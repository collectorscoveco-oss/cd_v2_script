# SonarDeck UI Technology Direction

The current Virtual Controller is Python/Tkinter. It is useful for fast testing because it has no extra UI dependency and runs easily from the existing bridge, but it is not the ideal long-term UI toolkit for a polished commercial-feeling app.

## Current decision

Keep the Tkinter app as the working V1 control/debug surface while the Sonar actions, page mappings, updater, and Arduino bridge are still moving quickly.

Start planning a proper UI migration once the control model stabilizes.

## Recommended next stack

### Best long-term direction: Tauri + React/TypeScript + Python bridge

- Modern app UI, close to Stream Deck / Raycast / SteelSeries quality.
- Small desktop app compared with Electron.
- Easy tabbed settings, icons, animations, version/about screens, and hardware status panels.
- Keep Python for the Sonar/serial/action bridge instead of rewriting all working control code at once.
- UI talks to the local bridge over HTTP/WebSocket or a local command interface.

### Simpler middle step: CustomTkinter

- Still Python.
- Much better-looking than raw Tkinter.
- Less work than Tauri.
- Good if we want a nicer V1 without building a full frontend stack.

### Not recommended for final polish: raw Tkinter only

Tkinter is fine for testing, but it is showing limits: click/focus artifacts, harder custom styling, and crowded layout once we add tabs, icons, and professional setup flows.

## Migration path

1. Keep current Tkinter app working and stable.
2. Move more logic into bridge modules that are UI-independent.
3. Add a local bridge API for actions, profiles, Sonar status, config save/load, and hardware events.
4. Build a Tauri/React UI that consumes the bridge API.
5. Keep the Tkinter app as a fallback/debug tool until the new UI is ready.

## Features that deserve the new UI

- real tabbed right panel
- icon/emoji/image support per button
- drag-and-drop button rearranging
- profile/page manager with reorder/delete
- hardware status page
- first-run setup wizard
- version/about/update screen
- packaged installer/desktop shortcut
- app-like animations without flicker
