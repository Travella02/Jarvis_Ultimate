# Jarvis Ultimate 0.2.1 — Orb Realism + Caption/Transition Polish

## What changed

- Brightened sleep mode so Jarvis still looks asleep, but the orb/rings/particles remain visible.
- Reworked the center orb into a more realistic 3D glass-like sphere instead of the older bullseye/core look.
- Added a few more subtle particles around the orb.
- Kept ring and particle geometry stable between states so the positions/directions do not jump.
- Added JavaScript-interpolated state colors so state changes fade instead of snapping.
- Kept speaking based on color + ring speed instead of outward wave effects.
- Removed the `Jarvis Output` label and the caption box under the orb.
- Centered the spoken caption text under Jarvis.
- Tightened caption timing so a new spoken response clears the old text and types fresh.
- Made Orb Only mode cleaner by hiding the top bar and the core-stage panel border/background.
- Added more natural sleep acknowledgements:
  - `thank you jarvis` / `thanks jarvis` -> `Of course, sir.` then sleep silently.
  - `that's all jarvis` / sleep phrases -> `Okay, sir.` then sleep silently.
- Updated app shell version to `0.2.1`.

## Notes

This patch does not change the Node/Electron dependency setup. No `npm install` should be needed if the app shell already launched on your machine.
