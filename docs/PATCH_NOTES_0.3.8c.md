# Jarvis Ultimate 0.3.8c — Responsive Window Resize

This patch continues the safe 0.3.8 UI stabilization path after the committed 0.3.8b checkpoint.

## What changed

- Added viewport-aware bounds for floating workspace panels.
- Floating panels now clamp back inside the visible Jarvis app window when the window is resized, maximized, restored, or made smaller.
- Drag and resize completion now re-clamps the active panel before saving the persisted layout.
- Window resize handling is debounced with `requestAnimationFrame` so the layout is not repeatedly reapplied during every tiny resize event.
- Resize handling waits while a panel is actively being dragged or resized so it does not fight the user's pointer movement.
- Removed the older small-window rule that forced floating panels into relative layout flow, because that could make panels jump or reflow weirdly during responsive transitions.
- Added responsive CSS guards for smaller/narrower windows while keeping the 0.3.8b panel header containment behavior.
- Updated app-shell version to `0.3.8c`.
- Added tests for responsive panel resize clamping.

## What this patch intentionally does not change

- Does not add Save Preset yet.
- Does not redesign the panel styling.
- Does not change memory, voice, LLM routing, agents, STT, or TTS behavior.
- Does not replace first-pass popouts with true dedicated Electron popout BrowserWindows yet.

## Files changed

- `app_shell/renderer/renderer.js`
- `app_shell/renderer/styles.css`
- `src/jarvis/clients/app_shell/bridge.py`
- `tests/unit/test_app_shell_responsive_layout_038c.py`
- Version-pinned app-shell tests
- `JARVIS_ULTIMATE_HANDOFF_INSTRUCTIONS.md`

## Validation completed

```powershell
node --check app_shell/renderer/renderer.js
python -m unittest discover -s tests -v
```

Result:

```text
Ran 433 tests in 5.139s

OK
```
