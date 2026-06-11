# Patch Notes — 0.1.6b Futuristic UI Theme + Panel System

## Goal
Make the Jarvis desktop body feel more modern and futuristic while keeping the UI modular enough for future tools, agents, and panels.

## Added
- Theme token system with built-in themes:
  - `jarvis_dark`
  - `cyber_blue`
  - `stealth_black`
- State-aware avatar/orb colors for:
  - sleeping
  - wake-listening
  - listening
  - transcribing
  - thinking
  - speaking
  - working
  - idle
  - error
- More futuristic desktop layout:
  - header bar
  - larger avatar/orb area
  - cleaner panel cards
  - improved workspace/event panels
  - better text spacing and monospace readouts
- Drop-in panel registry expansion for future UI surfaces:
  - reminders
  - web results
  - generated images
  - file results
  - screen context
  - agent dashboard
- Framework-neutral UI component formatting helpers.
- Workspace state helpers for opening, closing, summarizing, and snapshotting panels.

## Changed
- `scripts/start_jarvis.py` still launches the real desktop runtime.
- The UI remains a client/body, not the Jarvis brain.
- The CLI/headless runtime remains supported.

## Why this matters
This prepares Jarvis for future features where agents can open rich panels inside Jarvis’s interface instead of only returning chat text. Later tools can show reminders, web results, image previews, screen/OCR context, files, and agent activity in a modular workspace.

## Notes
This is still a Tkinter foundation. It is intentionally dependency-free and easy to run. A future version can swap the rendering layer to a more advanced UI stack while keeping the same workspace/panel state model.
