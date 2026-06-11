# Patch Notes — 0.1.6d Advanced Solid Orb Renderer

## Summary
0.1.6d upgrades the desktop avatar from a flat line-art orb into a more solid, dimensional, state-reactive Jarvis core.

## Added
- Framework-neutral `jarvis.ui.orb_renderer` helpers.
- Layered pseudo-3D solid orb renderer for the Tkinter desktop UI.
- State-reactive orb palettes for sleeping, listening, thinking, speaking, working, idle, and error states.
- Rotating orbital ring plans and particle orbit helpers.
- Stronger central-core status text that identifies the solid orb renderer.
- Unit tests for the orb rendering helpers and desktop renderer integration.

## Notes
This is still a Tkinter/canvas renderer, not a full WebGL/real-time 3D engine. It is meant to make the orb feel more alive now while keeping the architecture ready for a future true 3D renderer.
