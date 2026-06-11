# Jarvis Ultimate 0.1.8 Patch Notes

## Native App Shell Voice Bridge

This update connects the new Electron app-shell interface to Jarvis's real voice pipeline.

### Added

- Added direct app-shell voice API routes:
  - `GET /api/voice/status`
  - `POST /api/voice/once`
  - `POST /api/voice/sleep-wake/start`
  - `POST /api/voice/stop`
- Added background voice session management so the UI can stay open and keep refreshing while Jarvis listens, thinks, and speaks.
- Added a real **Listen Once** button to run the existing microphone -> STT -> LLM -> TTS path from the Electron UI.
- Added a real **Start Sleep/Wake** button to start app-controlled always-listening mode from the Electron UI.
- Added a **Stop Voice** button to request voice-mode shutdown and stop/clear pending TTS output.
- Added live voice session fields to `/api/state` snapshots:
  - mode
  - running/thread status
  - last transcript
  - last command
  - last response
  - handled/ignored/failure counts
  - stop-request status
- Added voice status display inside the orb stage.
- Added app-shell capabilities for real voice controls.
- Added automated tests for the app-shell voice bridge.

### Changed

- Updated app-shell version from `0.1.7` to `0.1.8`.
- Updated the local API server label from `JarvisLocalAPI/0.1.7` to `JarvisLocalAPI/0.1.8`.
- App-shell polling is slightly faster so visual state changes feel more reactive during voice sessions.

### Notes

This does not replace the older Tkinter desktop body yet. The Electron shell is now becoming the real main interface, but the Tkinter fallback remains available if Electron dependencies are missing.

