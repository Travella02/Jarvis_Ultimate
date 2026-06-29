# Jarvis Ultimate 0.3.8c2 — Workspace Safe Scaling Hotfix

This hotfix follows `0.3.8c1` and keeps the improved panel dragging, active panel priority, and content containment intact.

## What changed

- Floating panels now scale inside the actual workspace area below the top control bar, not against the full app window.
- Maximizing and restoring the Jarvis window should preserve floating panel proportions without letting panels cover the top controls.
- Floating panel bounds now track the `interfaceGrid` safe area using its live screen rectangle.
- Saved panel layout viewport data now includes `left`, `top`, `width`, and `height` so restore/maximize scaling can preserve relative position more accurately.
- Old `0.3.8c1` saved viewport data is ignored by using a new `0.3.8c2` viewport storage key. Existing panel positions are clamped into the safe workspace on first launch after applying the patch.
- App shell version is now `0.3.8c2`.

## Why this was needed

Live testing showed that after maximizing and restoring, panels could keep the maximized-style placement and overlap the top control panel. The previous resize guard kept panels inside the full window, but the correct safe area is the workspace below the top control bar.

## What did not change

- No visual redesign was added.
- No Save Preset behavior was added yet.
- No real Electron pop-out window redesign was added yet.
- The existing lock, dock, pop, drag, resize, and active-panel stacking behavior remains intact.

## Next recommended step

After manual testing succeeds, commit `0.3.8c2`. Then continue to `0.3.8d — Save Custom Preset`, or do one more tiny layout hotfix if maximize/restore still has an edge case.
