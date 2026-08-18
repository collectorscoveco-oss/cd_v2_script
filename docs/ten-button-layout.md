# SonarDeck 10-Button Layout Direction

Based on the user's reference image, the preferred physical direction is closer to Console Deck V2:

- a 3x3 grid of square app/action buttons on the left
- a large volume knob on the right
- a wide dedicated play/pause button at the lower-right
- the play/pause button is treated as Button 10

## Event model

Button 10 is dual-purpose:

```text
BTN_10_PRESS  Play/Pause
BTN_10_LONG   Switch profile/page
```

This keeps the normal 9-button deck grid clean and gives the oversized media button a hidden long-press page-switch behavior.

## Current software mapping

- `BTN_01_PRESS` through `BTN_09_PRESS`: normal mappable deck buttons
- `BTN_10_PRESS`: `media.play_pause`
- `BTN_10_LONG`: `profile.next`
- `ENC_01_CW`: Windows volume up
- `ENC_01_CCW`: Windows volume down
- `ENC_01_PRESS`: Windows mute

## Firmware note

The firmware now includes a placeholder Button 10 pin:

```cpp
A2 // BTN_10 - dedicated play/pause; long press switches profile/page
```

This pin can be changed once the final Arduino Nano wiring and printed case layout are confirmed.

## UI note

The modern React UI displays Button 10 as a wider play/pause card. Short click fires play/pause; holding it for about 650 ms sends `BTN_10_LONG` and switches pages.

## Physical design notes

Do not commit to final hole sizes until the actual parts are measured:

- button cap dimensions
- knob diameter and encoder nut diameter
- OLED module size if used later
- Arduino Nano mounting/USB clearance
- case wall thickness and print orientation
