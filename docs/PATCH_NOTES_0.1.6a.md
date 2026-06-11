# Patch Notes — 0.1.6a Desktop Full Runtime Launcher

## Summary

0.1.6a connects the desktop UI to the real Jarvis voice runtime and adds a one-file startup path for daily use.

The desktop UI is still a client/body, not the brain. Jarvis Core remains headless-capable, and the CLI still works.

## Added

- Desktop UI can run the real sleep/wake voice runtime in a background thread.
- Desktop UI can auto-start voice mode after boot when configured.
- Desktop UI buttons:
  - Start Voice
  - Stop Voice
  - Warm Up
- Desktop UI typed shortcuts:
  - `start voice`
  - `stop voice`
  - `warmup`
- Desktop status now shows:
  - voice runtime running/stopped
  - latest voice status
  - auto-start setting
- Background voice runtime updates:
  - chat panel with heard transcripts
  - chat panel with streamed Jarvis responses
  - avatar states for wake-listening, listening, transcribing, speaking, sleeping, and error
  - event log through `ui.voice_status`
- `scripts/start_jarvis.py` as the normal full-start launcher.
- `Start_Jarvis_Ultimate.bat` for Windows double-click/start-from-root use.
- `scripts/run_desktop.py` now uses the same robust source-path setup as other launchers.

## Changed

- `JarvisRuntime.voice_sleep_wake_loop()` now accepts an optional external `stop_event` so UI clients can request shutdown without killing the process.
- `.env.example` documents desktop voice auto-start settings.
- `config/ui.yaml` now treats desktop as the default client/body and records voice auto-start defaults.

## New config

```env
JARVIS_DESKTOP_AUTO_START_VOICE=true
JARVIS_DESKTOP_VOICE_START_MODE=sleep_wake
```

## Design note

This patch is a bridge toward Jarvis being a normal always-running desktop presence. The UI can now be the place where Jarvis listens, sleeps/wakes, speaks, shows status, and later opens dynamic panels for screen context, files, images, reminders, web results, and tools.

## Tests

Validated with:

```powershell
python -m unittest discover -s tests -v
```

Result in clean test environment:

```text
Ran 167 tests
OK
```
