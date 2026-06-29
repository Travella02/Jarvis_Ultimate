# Testing Guide — Jarvis Ultimate 0.3.8c3

## 1. Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_8c3_independent_panel_drag_freeze_patch.py
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

1. Open Jarvis and make sure the panels load normally.
2. Move the Core Orb panel. The Conversation panel should stay exactly where it was.
3. Move the Conversation panel. The Core Orb panel should stay exactly where it was.
4. Resize one floating panel. Other floating panels should not move, resize, or snap.
5. Click overlapping panels and confirm the last clicked panel comes to the front.
6. Maximize and restore the Jarvis window. Panels should still follow the workspace bounds from 0.3.8c2.
7. Use Reset Layout once only if an old saved layout still looks strange, then retest the same steps.

## Success looks like

- Dragging one panel only moves that panel.
- Resizing one panel only resizes that panel.
- No nearby panel jumps to the middle of the screen.
- The Conversation panel does not go behind the Core Orb unless you intentionally click/move the Core Orb to the front.
- Panel buttons remain visible and non-overlapping.

## Common issues

- If panels still appear in strange places immediately after applying the patch, click **Reset Layout** once. Old saved layout data can still contain bad positions from earlier tests.
- If one panel visually covers another, click the panel you want to use. The last active panel should come to the front.
- If moving one panel still causes another panel to move after Reset Layout, capture a screenshot and note which two panels were involved.
