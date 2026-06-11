# Patch Notes — 0.1.6 Desktop UI + Avatar Workspace Foundation

## Summary
0.1.6 gives Jarvis his first real desktop interface/body while keeping Jarvis Core headless-capable. The UI is intentionally modular so future agents can open their own panels inside Jarvis's interface without rewriting the desktop shell.

## Added
- `scripts/run_desktop.py`
- `scripts/run_desktop_ui.py` now launches the same desktop shell
- Tkinter-based desktop UI shell with no new dependency requirements
- Avatar/orb placeholder panel
- Chat panel with typed command input
- Runtime status panel
- Agent status panel
- Event log panel
- Workspace panel for future dynamic cards
- Framework-neutral `UIWorkspaceState`
- Drop-in `UIPanelRegistry` and `UIPanelSpec`
- UI event helpers for future `ui.open_panel` and `ui.update_panel` events
- Expanded avatar states:
  - `sleeping`
  - `wake_listening`
  - `listening`
  - `transcribing`
  - `thinking`
  - `speaking`
  - `working`
  - `idle`
  - `error`

## Why this matters
This is the foundation for Jarvis's future visual workspace/control center. Later, agents can show reminders, web results, generated images, files, screen context, OCR output, calendar cards, and debug panels inside Jarvis's interface.

## Architecture rule preserved
The UI is Jarvis's body/client, not his brain.

Jarvis Core still runs from:

```powershell
python scripts/run_cli.py
```

The desktop body runs from:

```powershell
python scripts/run_desktop.py
```

## Not included yet
- Always-listening inside the desktop UI window
- Screen capture display
- OCR display
- Real dynamic tool cards from agents
- Live2D/VRM avatar rendering
- Barge-in controls

Those should build on this foundation.
