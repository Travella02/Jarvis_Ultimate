# Jarvis UI Central Orb State Engine

## Purpose

0.1.6c makes the orb the visual center of Jarvis Ultimate.  The current renderer is still a dependency-free Tkinter canvas, but the architecture now treats the orb as a state-driven avatar core that can later be replaced with a richer renderer such as WebGL, Three.js, Qt/QML, Live2D, or a real 3D avatar layer.

## Layout Direction

The desktop body now uses a central-orb workspace layout:

- center: Jarvis orb/avatar core and conversation
- left: runtime status and event stream
- right: modular workspace panels

The goal is that future tools open around Jarvis instead of replacing Jarvis.  Reminders, web results, generated images, files, screen/OCR context, and agent dashboards should all be able to open as drop-in panels while the orb remains the main visual presence.

## Visual States

The shared visual state engine lives in:

```text
src/jarvis/ui/visual_state.py
```

Supported visual states:

- `sleeping`
- `wake_listening`
- `listening`
- `transcribing`
- `thinking`
- `speaking`
- `working`
- `idle`
- `error`

Each state maps to an `OrbVisualProfile` with:

- label
- color role
- pulse speed
- ring speed
- core scale
- glow strength
- particle count
- breathing behavior

## Future Renderer Path

The current Tkinter canvas uses circles, arcs, particles, and pulse math to simulate a holographic 3D orb.  A future renderer should consume the same visual state/profile model and render it with better visuals.

Possible future renderers:

- HTML/WebView + Canvas/WebGL
- Three.js central orb
- Qt/QML animated interface
- Live2D/VRM avatar provider
- dedicated game-engine style renderer

## Design Rule

Jarvis Core remains the brain.  The UI remains the body/workspace.  The avatar renderer should react to events and state changes, not own the assistant's decision-making.
