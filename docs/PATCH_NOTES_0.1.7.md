# Patch Notes — 0.1.7 Native App Shell Foundation

## Summary
0.1.7 starts moving Jarvis from the Tkinter-only desktop body toward the real main-interface direction: an HTML/CSS/JavaScript visual interface wrapped in a native Electron desktop app shell, with a local Python API bridge back into the existing Jarvis runtime.

This keeps the current Tkinter desktop UI as a fallback, but introduces the path for the main Jarvis interface to become a real app window instead of a browser page.

## Added
- New `app_shell/` Electron app foundation.
- HTML/CSS/JavaScript orb interface with smooth state-reactive visual classes.
- Electron `main.js` and `preload.js` so the UI opens as a desktop app window.
- Local Python API bridge using only the standard library:
  - `GET /api/health`
  - `GET /api/state`
  - `GET /api/events`
  - `POST /api/command`
- New app-shell bridge helpers in `jarvis.clients.app_shell.bridge`.
- New `scripts/start_jarvis_app.py` launcher that starts the local API and opens Electron when dependencies are installed.
- New `scripts/start_local_api_server.py` for API-only testing/debugging.
- New `Start_Jarvis_Ultimate_App.bat` Windows launcher.
- Tests for the app-shell snapshot contract, local API bridge, and Electron asset foundation.
- Documentation for the app-shell architecture.

## Changed
- The existing Tkinter desktop body remains intact and still passes previous UI/orb tests.
- The new app-shell launcher falls back to the existing Tkinter UI if Electron dependencies are not installed yet.
- The UI direction is now explicitly split:
  - Python runtime/core = Jarvis brain and systems
  - Electron HTML/CSS/JS app shell = Jarvis main interface/body

## Notes
This patch is a foundation, not the finished final Jarvis interface. The app shell now exists, can open as a native app after `npm install`, and has API hooks for state and commands. The next UI work can focus on making the Electron orb feel more alive, adding real panel rendering, and eventually moving voice controls into the app shell.
