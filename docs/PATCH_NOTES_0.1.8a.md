# Jarvis Ultimate 0.1.8a Patch Notes

## Name
App Shell Voice Readiness and Layout Hotfix

## Why this patch exists
0.1.8 connected the Electron app shell to the real Jarvis voice bridge, but real testing showed three problems:

1. The orb switched out of the speaking state too early.
2. The voice control buttons could slide underneath the conversation panel.
3. Jarvis needed a stronger voice warmup gate before being considered ready for conversation.

## What changed

### Speaking state now tracks real playback
- The one-turn voice bridge now waits for the spoken response pipeline to finish playback before marking the turn idle.
- The app shell keeps the avatar in `speaking` while Jarvis is finishing TTS playback.
- Speech-related runtime events now reinforce the speaking visual state inside the app-shell API bridge.

### Voice controls stay visible
- Reduced the central orb size enough to leave room for controls.
- Changed the core panel to scroll internally instead of overflowing behind the bottom conversation panel.
- Hid the old demo state buttons now that the app shell is connected to real voice controls.
- Added a more compact state message layout so long responses do not push controls out of view.

### Voice warmup gate
- The app-shell API now warms voice systems before voice conversation controls are considered ready.
- If normal runtime boot already performed voice warmup, the app shell reuses that warmup summary instead of doing unnecessary duplicate work.
- The UI now shows a warmup readiness field in the voice status card.

## Files changed
- `src/jarvis/api/local_server.py`
- `src/jarvis/core/lifecycle.py`
- `src/jarvis/clients/app_shell/bridge.py`
- `app_shell/renderer/index.html`
- `app_shell/renderer/renderer.js`
- `app_shell/renderer/styles.css`
- `tests/unit/test_app_shell_voice_bridge_018.py`
- `docs/PATCH_NOTES_0.1.8a.md`
- `docs/TESTING_GUIDE_0.1.8a.md`

## Expected behavior after applying
- Jarvis should not visually return to idle until speech playback is finished.
- Listen Once / Start Sleep-Wake / Stop Voice should stay reachable and not hide behind the conversation panel.
- The voice card should show warmup readiness.
- Voice controls should only enable once the local voice systems are ready.
