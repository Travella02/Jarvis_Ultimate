# Testing Guide — Jarvis Ultimate 0.3.8b

## 1. Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_8b_panel_stability_patch.py
```

## 2. Run the test suite

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

### Header button overlap

Check the Runtime and Workspace panels in the left rail.

Expected:

- Hide, Lock, Min, Dock, and Pop are all visible.
- No button text sits on top of another button.
- The panel title does not cover the buttons.
- The Lock button stays the same width when toggled.

### First drag stabilization

Make sure the global layout says `Layout: Unlocked`, then drag the Runtime or Workspace panel.

Expected:

- The dragged panel becomes floating.
- Nearby panels should not suddenly balloon larger while you are dragging.
- Nearby panels should not stack on top of each other during the drag.
- The dragged panel should stay under your pointer.

### Per-panel lock still works

Click Lock on a panel and try to drag or resize it.

Expected:

- Locked panels should not drag.
- Locked panels should not resize.
- Unlocked panels should still drag and resize.

### Layout preset dropdown readability

Open the Layouts dropdown.

Expected:

- Gaming, Coding, Music, and Minimal should be readable without needing to hover each option.

## 5. Common outcomes

If a panel still acts weird, click `Reset Layout`, close Jarvis, restart it, and test again. If a specific panel still overlaps buttons after reset, take a screenshot before moving anything so we can target that exact panel next.
