# Jarvis Ultimate 0.2.0 — Orb Motion + Speech Caption Polish

## What changed

- Made the app background nearly pure black.
- Made panels feel more holographic by keeping mostly transparent fill and emphasizing blue edge/glass lines.
- Reworked orb ring motion so ring orientation and position stay stable across states.
- Added continuous JavaScript-driven ring/orb motion to prevent CSS animation restarts from causing glitches during state changes.
- Added smoother speed blending between sleep, idle, listening, thinking, speaking, and error states.
- Kept sleep mode grey, but added subtle breathing and slow ring/particle motion so Jarvis still feels alive while asleep.
- Removed speaking wave visuals and kept speaking focused on ring speed and blue shade changes.
- Added an under-orb Jarvis speech caption with a futuristic typewriter effect.
- Added live response text from the app-shell voice bridge so the caption can update while Jarvis is speaking.
- Refined Orb Only mode so the state label, status message, bridge strip, and extra panels hide, leaving the orb and Jarvis output caption.
- Added Escape key support to exit Orb Only mode.
- Updated app-shell version to 0.2.0.

## Updated files

- `app_shell/renderer/index.html`
- `app_shell/renderer/styles.css`
- `app_shell/renderer/renderer.js`
- `src/jarvis/api/local_server.py`
- `src/jarvis/clients/app_shell/bridge.py`
- app-shell UI/unit tests

## Notes

No `npm install` should be needed for this patch because it only changes renderer, API bridge, and test files.
