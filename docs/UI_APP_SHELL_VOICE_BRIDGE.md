# UI App-Shell Voice Bridge

Version: 0.1.8

The app-shell voice bridge lets the Electron interface control Jarvis's real Python voice runtime without becoming a browser-based UI.

## Main flow

The desktop app starts like this:

1. `python scripts/start_jarvis_app.py`
2. Python starts the local Jarvis API on `127.0.0.1:8765`.
3. Electron opens `app_shell/renderer/index.html` in a native desktop window.
4. The renderer polls `/api/state` and sends actions to the local API.
5. The local API calls the existing `JarvisRuntime` voice systems.

## Voice controls

The Electron renderer now has three real voice controls:

- **Listen Once**: starts one voice turn using `runtime.voice_loop_once()`.
- **Start Sleep/Wake**: starts app-shell controlled sleep/wake mode in a background thread.
- **Stop Voice**: requests the background voice session to stop and clears pending TTS output.

## API routes

### `GET /api/voice/status`

Returns the current voice session plus the normal app-shell state snapshot.

### `POST /api/voice/once`

Starts one microphone turn in the background.

Optional JSON body:

```json
{
  "speak": true,
  "mode": "smart",
  "silence_seconds": 0.65,
  "duration_seconds": null
}
```

### `POST /api/voice/sleep-wake/start`

Starts sleep/wake mode from the app shell.

Optional JSON body:

```json
{
  "max_turns": 0,
  "active_timeout_seconds": 45,
  "speak": true,
  "mode": "smart",
  "silence_seconds": 0.65
}
```

`max_turns: 0` means unlimited until the user presses **Stop Voice** or says an exit phrase.

### `POST /api/voice/stop`

Requests the active voice session to stop after the current microphone turn and clears pending TTS output.

## Important behavior

The stop button cannot instantly cut off a microphone recording that is already in progress because the STT recorder must return control first. It will stop the session at the next safe checkpoint.

