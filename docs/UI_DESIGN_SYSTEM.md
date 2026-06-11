# Jarvis UI Design System

Jarvis’s UI is meant to become his visual body and workspace, not the brain.
Core Jarvis must still run headless, while desktop/web/avatar clients can connect to the same runtime.

## Principles

- Jarvis Core remains modular and headless-capable.
- The UI is a client/body.
- Agents and tools should be able to open panels with events.
- Panels should be drop-in, like agents and providers.
- Theme tokens should be shared across future desktop/web/avatar clients.

## Theme tokens

Built-in themes live in `src/jarvis/ui/themes.py`.

Current themes:

- `jarvis_dark`
- `cyber_blue`
- `stealth_black`

Important tokens include:

- `background`
- `surface`
- `panel`
- `panel_alt`
- `panel_border`
- `panel_glow`
- `text`
- `muted`
- `accent`
- `success`
- `warning`
- `error`

## Avatar states

Current supported states:

- `sleeping`
- `wake_listening`
- `listening`
- `transcribing`
- `thinking`
- `speaking`
- `working`
- `idle`
- `error`

Future avatar systems, including an animated orb, Live2D model, or VRM body, should react to the same state names.

## Drop-in panels

Default registry lives in `src/jarvis/ui/panels.py`.

Future agents can open panels with events such as:

```python
runtime.events.emit(
    "ui.open_panel",
    source="screen_agent",
    message="Screen context ready.",
    data={
        "panel_id": "screen_context",
        "title": "Screen Context",
        "payload": {"active_window": "Studio One"},
    },
)
```

Future panel ideas:

- reminders
- web results
- generated images
- file results
- screen/OCR context
- weather cards
- calendar cards
- agent dashboards
- debug timing panels

## Current rendering layer

The desktop UI currently uses Tkinter to avoid extra dependencies. Later, a more advanced rendering layer can replace it while keeping the same framework-neutral workspace state.
