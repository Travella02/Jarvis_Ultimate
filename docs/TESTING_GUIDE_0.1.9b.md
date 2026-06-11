# Testing Guide — 0.1.9b Holographic Interface and Sleep Mode Hotfix

## Automated tests

From the project root, run:

```powershell
python -m unittest discover -s tests -v
```

Expected result: all tests pass.

## Manual checks

Launch Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

Check the following:

1. The left voice panel should not have hidden buttons or a horizontal scrollbar.
2. Sleep/wake mode should look like a dim, constant grey orb with slow movement.
3. The background should be nearly pitch black.
4. Panels should look like transparent blue holographic glass.
5. When Jarvis changes modes, the colors should fade/blend instead of instantly snapping.
6. Auto Wake should still start sleep/wake after warmup, unless you turned Auto Wake off.

## Cleanup before committing

```powershell
Remove-Item .\apply_0_1_9b_holographic_sleep_patch.py -Force
Remove-Item .\patch_files -Recurse -Force
```
