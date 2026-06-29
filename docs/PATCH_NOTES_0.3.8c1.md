# Patch Notes — Jarvis Ultimate 0.3.8c1

## Window State Panel Follow + Active Panel Priority Hotfix

This hotfix follows live testing of 0.3.8c and fixes the remaining layout behavior Tanner found when maximizing/restoring Jarvis and resizing panels.

## What changed

- Floating panel layouts now remember the viewport size they were saved against.
- Existing 0.3.8c saved layouts can infer an initial viewport from floating-panel coordinates.
- When the Jarvis window is maximized, restored, or resized, floating panels scale proportionally with the new viewport instead of staying stuck in the old window-size coordinates.
- Floating panels still clamp inside the visible app window after scaling.
- The last active panel now has priority. Clicking, dragging, or resizing a panel brings that panel to the front.
- Runtime and other floating panels now have safer minimum restored sizes.
- Runtime panel text and status rows are contained with scroll/word wrapping so long model names should not spill outside the panel when the panel is small.
- Added regression coverage for viewport-scaling, panel z-order priority, and runtime panel content containment.
- App shell version is now `0.3.8c1`.

## What did not change

- No Save Preset button yet.
- No real Electron popout rewrite yet.
- No visual polish pass yet.
- No memory, voice, app-agent, or LLM routing behavior changed.

## Validation

- `node --check app_shell/renderer/renderer.js`
- `python -m unittest discover -s tests -v`
- Result: `Ran 437 tests in 3.635s — OK`
