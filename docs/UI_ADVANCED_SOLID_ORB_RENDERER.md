# UI Advanced Solid Orb Renderer

0.1.6d introduces a stronger visual identity for Jarvis's central avatar core.

The renderer is still implemented with Tkinter canvas primitives, but it uses a modular helper layer so future renderers can replace it without changing the desktop runtime or Jarvis brain.

## Renderer goals
- Make the orb look more solid and dimensional.
- Preserve state-driven behavior.
- Support stronger visual differences between sleeping, listening, thinking, speaking, working, and error states.
- Keep the future path open for WebGL, Qt/QML, or another true 3D renderer.

## Current effects
- layered solid sphere
- pseudo-3D highlight and shadow
- rotating orbital rings
- particle sparks
- state-reactive palettes
- state-reactive pulse/ring speed

## Future renderer path
The UI can later replace the Tkinter canvas renderer with a richer engine while keeping the same state model:

```text
Jarvis runtime events
→ workspace/avatar state
→ visual state engine
→ renderer profile
→ Tkinter now / WebGL later / Qt later
```
