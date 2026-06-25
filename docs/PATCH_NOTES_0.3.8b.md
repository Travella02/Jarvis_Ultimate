# Jarvis Ultimate 0.3.8b — Panel Header Containment + First Drag Stabilization

This hotfix follows manual testing of 0.3.8a. It keeps the reset 0.3.8 dockable workspace baseline and the 0.3.8a per-panel Lock button, but fixes the visible overlap and first-drag instability problems.

## What changed

- Panel header action buttons now wrap safely instead of overlapping each other or the panel title.
- Left-rail panels now use a safer stacked header layout so Hide / Lock / Min / Dock / Pop stay visible.
- The Lock button no longer grows from `Lock` to `Locked`, which reduces header width pressure while still showing active lock state through styling.
- Layout preset dropdown options now have explicit dark menu background and readable text.
- First drag/resize of a docked panel now uses an invisible placeholder so nearby panels do not suddenly expand, stack, or jump while the dragged panel is being promoted to floating mode.
- Drag/resize now promotes the active panel to floating without reapplying the whole layout during pointer-down.
- App shell version is now `0.3.8b`.

## Validation completed

```powershell
node --check app_shell/renderer/renderer.js
PYTHONPATH=src python -m unittest discover -s tests -v
```

Result:

```text
Ran 430 tests in 4.883s

OK
```

## Manual focus

After applying, test the Runtime and Workspace panels first. Their buttons should never overlap. Then unlock the layout and drag one left-side panel for the first time. The nearby panels should no longer balloon or try to stack on top of each other while dragging.
