# Jarvis Native App Shell

0.1.7 introduces the first native app-shell foundation for Jarvis Ultimate.

## Why this exists
The goal is for Jarvis to have a real main interface that opens like an app, not like a browser tab. The Python runtime remains the brain. The app shell becomes the body/interface.

## Current architecture

```text
Jarvis Python runtime
  └─ local standard-library HTTP API
      └─ Electron desktop window
          └─ HTML/CSS/JavaScript orb interface
```

## What each layer does

### Python runtime
- Boots Jarvis.
- Handles commands.
- Owns agents, LLM, STT, TTS, wake word, memory, events, and workspace state.

### Local API bridge
- Serves state to the app shell.
- Accepts typed commands from the app shell.
- Keeps the UI separate from the core runtime.
- Uses Python standard library only.

### Electron app shell
- Opens as a native desktop app.
- Loads the HTML/CSS/JS renderer.
- Talks to the local Python API.
- Does not require the interface to be a browser tab.

## Current API routes

```text
GET  /api/health
GET  /api/state
GET  /api/events
POST /api/command
```

## Current launcher

```powershell
python scripts/start_jarvis_app.py
```

This starts the local API bridge and launches Electron when `app_shell/node_modules/electron` exists.

If Electron is not installed yet, it explains the setup step and opens the existing Tkinter desktop fallback.

## Next steps
Good next patches after this foundation:

1. Improve Electron orb realism and animation smoothness.
2. Add real app-shell voice controls.
3. Add live event streaming instead of polling.
4. Render workspace cards as real UI panels.
5. Move the app shell closer to the final Jarvis main interface.
