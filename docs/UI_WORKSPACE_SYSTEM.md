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
