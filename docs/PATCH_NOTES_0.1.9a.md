# Jarvis Ultimate 0.1.9a Patch Notes

## Native app shell interface control hotfix

This update refines the 0.1.9 main interface based on live UI testing.

### Fixed

- Fixed left rail panel overlap by changing the left side from rigid grid rows to a scroll-safe stacked rail.
- Prevented voice/status cards from pushing workspace controls into the bottom diagnostics area.
- Preserved the app's diagnostics collapsed/open state without destroying the rest of the body classes.

### Improved

- Added slower, smoother visual transitions between Jarvis modes.
- Reworked the state color palette:
  - Idle/main Jarvis: blue
  - Sleep/wake waiting: dim grey-blue
  - Listening/transcribing: brighter cyan-blue
  - Speaking: deeper voice-blue
  - Thinking: purple
  - Error: red
- Sleep/wake waiting now visually behaves like sleep mode instead of active listening.
- Sleep mode dims the orb and slows halo/ring/particle motion.
- Speaking, listening, thinking, and error states now transition with less abrupt color and animation changes.

### Added

- Panel visibility controls in the top bar.
- Hide buttons on Runtime, Voice, Workspace, Conversation, and Diagnostics panels.
- Orb-only focus mode so Jarvis can be displayed with just the core orb interface.
- Persistent panel visibility using local storage.
- Automatic sleep/wake startup from the app shell after bridge and voice warmup are ready.
- Auto Wake toggle in the top bar.

### Notes

Auto Wake starts sleep/wake mode once per app launch. If you press Stop Voice, Jarvis will not immediately restart sleep/wake until you manually start it again or toggle Auto Wake.
