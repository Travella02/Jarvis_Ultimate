# Testing Guide — Jarvis Ultimate 0.3.8c

This test pass is focused on responsive window resizing only.

## 1. Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_8c_responsive_window_resize_patch.py
```

## 2. Run the automated tests

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## 3. Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

## 4. Manual checks

### Basic startup

- Jarvis should open normally.
- The app should still show version `0.3.8c` through the app-shell bridge/version tests.
- Runtime, Voice, Workspace, Chat, Diagnostics, and Orb Only controls should still work.

### Existing 0.3.8b behavior

- Panel buttons should not overlap.
- The Lock button should still prevent drag and resize for that panel.
- Unlocked panels should still drag and resize.
- First drag of a docked panel should not make nearby panels balloon or stack on top of each other.
- The layout preset dropdown text should still be readable.

### Responsive resize behavior

1. Move one or two panels so they are floating.
2. Resize the Jarvis window smaller.
3. Confirm floating panels stay reachable inside the app window.
4. Maximize Jarvis.
5. Restore Jarvis back to windowed mode.
6. Confirm panels do not disappear off-screen.
7. Resize a panel near the right/bottom edge and then make the window smaller.
8. Confirm the panel clamps back into view.

### Layout controls after resizing

- Press `Reset Layout` and confirm the default layout comes back cleanly.
- Try the Gaming, Coding, Music, and Minimal presets.
- Confirm panels do not explode, stack strangely, or disappear after changing presets.

## 5. What success looks like

This patch is successful if resizing, maximizing, restoring, and shrinking the Jarvis window does not strand floating panels off-screen and does not break the stable 0.3.8b panel control behavior.

## 6. If something looks wrong

- If a panel looks too cramped, press `Reset Layout` once and retest.
- If panel controls overlap again, stop and report a screenshot before applying another patch.
- If floating panels stay visible but styling looks imperfect, that is okay for now. Styling polish should happen later after layout behavior is stable.
