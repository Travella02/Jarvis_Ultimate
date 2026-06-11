# Jarvis Ultimate 0.1.9 Patch Notes

## Native App Shell Main Interface Polish

This update turns the Electron app shell from a dashboard-style test screen into a more Jarvis-first main interface.

## Added

- Cinematic three-zone app layout:
  - left rail for runtime, voice controls, and workspace panels
  - central orb stage as the main focus
  - right conversation dock for text interaction
- Collapsible diagnostics drawer so debug/event data does not dominate the main UI.
- Larger, more alive central orb presentation.
- State-specific orb motion:
  - calmer sleep/idle behavior
  - faster listening rings
  - faster thinking orbit motion
  - speaking wave pulses around the orb
  - alert shake for error state
- Startup readiness strip showing bridge, voice, and warmup status.
- Cleaner chat bubbles for user, heard, and Jarvis messages.
- Better responsive layout for smaller windows.

## Changed

- App-shell version is now `0.1.9`.
- Voice controls were moved into a dedicated left rail card instead of sitting under the orb.
- Event stream moved into a diagnostics drawer that starts collapsed.
- Conversation panel is now a primary dock instead of a lower dashboard panel.
- Main orb is larger and has a more cinematic background scan/radar effect.

## Why This Matters

Jarvis should feel like an app centered around the living orb, not a generic admin dashboard. This update keeps the important systems visible while making the actual Jarvis interface feel more focused and alive.
