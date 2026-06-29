# Testing Guide — Jarvis Ultimate 0.3.8c4

## 1. Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_8c4_release_safe_panel_geometry_freeze_patch.py
```

## 2. Run automated tests

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

## 4. Manual panel checks

1. Open Jarvis normally.
2. Put the Core Orb panel and Conversation panel near each other.
3. Drag only the Core Orb panel and release it.
4. The Conversation panel should stay exactly where it was before, during, and after release.
5. Drag the Conversation panel and release it.
6. The Core Orb panel should stay exactly where it was.
7. Resize one panel and release the mouse.
8. No other panel should move, snap, resize, or go behind another panel because of that action.
9. Maximize and restore Jarvis once to confirm the 0.3.8c2 scaling behavior still works.

## If a saved layout still looks strange

Click **Reset Layout** once inside Jarvis, then repeat the manual checks. Old saved layout coordinates from earlier 0.3.8 testing can still look odd until reset.
