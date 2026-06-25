# Testing Guide — Jarvis Ultimate 0.3.8a Panel Lock Only

## 1. Apply the patch

From the root of your Jarvis project, run:

```powershell
python apply_0_3_8a_panel_lock_only_patch.py
```

## 2. Run the unit tests

```powershell
python -m unittest discover -s tests -v
```

Success should end with something like:

```text
OK
```

## 3. Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

## 4. Manual UI checks

1. Open Jarvis and make sure the normal 0.3.8 workspace layout still loads.
2. Make sure each dockable panel now has a small **Lock** button beside **Min**, **Dock**, and **Pop**.
3. Make sure the top **Layout: Locked / Unlocked** button still works the same as before.
4. Set the top layout button to **Unlocked**.
5. Click **Lock** on only one panel, such as Workspace.
6. Try to drag or resize that locked panel.
7. Confirm that locked panel stays in place.
8. Try to drag or resize another unlocked panel.
9. Confirm the unlocked panel still moves normally.
10. Click the locked panel button again to unlock it.
11. Confirm it can be moved and resized again.

## 5. What this patch intentionally does not fix yet

This patch does not fix the dropdown text color, responsive resize behavior, save preset button, panel overlap, or real Electron popout windows. Those should stay as separate small patches so we do not break the layout system again.

## 6. Good result

A good result is:

- Tests pass.
- Jarvis starts normally.
- The UI is still the reset 0.3.8 baseline.
- Per-panel Lock buttons appear.
- Locked panels cannot be dragged or resized.
- Unlocked panels still behave like before.
