# Patch Notes — 0.1.6c Central Orb Layout + UI State Engine

## Summary

This patch moves the desktop UI toward Tanner's long-term Jarvis interface vision: the orb becomes the center of the UI, with status, events, chat, and workspace panels arranged around Jarvis instead of the orb living as a small side card.

## Added

- Central-orb desktop layout.
- Larger avatar/orb canvas.
- Framework-neutral UI visual state engine.
- Orb animation profiles for:
  - sleeping
  - listening for wake word
  - listening
  - transcribing
  - thinking
  - speaking
  - working
  - idle
  - error
- More advanced Tkinter orb renderer with:
  - pseudo-3D glass sphere
  - rotating orbital arcs
  - particle sparks
  - state-driven pulse/ring speeds
  - state labels
- Tests for the visual state engine and central layout.

## Design Notes

This is not the final realistic 3D orb yet. It is a stronger desktop layout and state engine foundation so a future WebGL/Three.js/Qt/QML/3D renderer can replace the current Tkinter canvas without rewriting the rest of Jarvis.

The UI still stays modular. Jarvis Core remains headless-capable, and future tools can continue opening panels through workspace/UI events.
