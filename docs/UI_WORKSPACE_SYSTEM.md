# Jarvis UI Workspace System

Jarvis's UI is intended to become his visual body and control center, not just a chat window.

## Core idea

Jarvis Core remains headless-capable. The UI is a client/body that reflects events and exposes panels.

```text
Jarvis Core / Brain
→ events + result objects
→ Desktop UI / Avatar Body
→ dynamic panels/cards
```

## Drop-in panels
Future agents should not rewrite the desktop window. They should emit standard UI events or register panel specs.

Examples:

```python
from jarvis.ui.ui_events import make_ui_open_panel_event

event = make_ui_open_panel_event(
    "web_results",
    title="Web Results",
    payload={"results": [...]},
)
```

Future panel examples:
- `reminders`
- `web_results`
- `generated_images`
- `file_results`
- `screen_context`
- `ocr_results`
- `calendar_events`
- `debug_timing`
- `agent_activity`

## Avatar states
The first desktop shell supports these state names:
- `sleeping`
- `wake_listening`
- `listening`
- `transcribing`
- `thinking`
- `speaking`
- `working`
- `idle`
- `error`

A future Live2D/VRM/orb renderer can use the same state names.

## Important rule
The UI must stay replaceable. Jarvis should always be able to run with:

```powershell
python scripts/run_cli.py
```

and with:

```powershell
python scripts/run_desktop.py
```

## 0.1.6a desktop full runtime launcher

The desktop UI can now connect to the same real Jarvis voice runtime used by the CLI. This keeps the architecture modular:

- Jarvis Core remains the brain.
- The desktop UI is a client/body.
- The sleep/wake voice runtime can run in a background thread while the UI stays responsive.
- Future UI panels can still be dropped in through workspace events.

Daily startup options:

```powershell
python scripts/start_jarvis.py
```

or on Windows:

```text
Start_Jarvis_Ultimate.bat
```

The desktop voice runtime can auto-start when these settings are enabled:

```env
JARVIS_DESKTOP_AUTO_START_VOICE=true
JARVIS_VOICE_ALWAYS_LISTENING_ON_STARTUP=true
JARVIS_VOICE_ALWAYS_LISTENING_MAX_TURNS=0
```

The UI exposes basic runtime controls:

- Start Voice
- Stop Voice
- Warm Up

This is still an early runtime bridge. Future UI versions should move toward a local API/WebSocket layer so the UI can connect/disconnect from a long-running Jarvis Core service instead of hosting the runtime in-process.
