# Testing Guide — 0.3.8d3 Custom-Only Layout Preset Management

## 1. Run unit tests

From the Jarvis project root, run:

```powershell
python -m unittest discover -s tests -v
```

Expected result: all tests pass.

## 2. Start Jarvis

After the tests pass, start the app shell:

```powershell
python scripts\start_jarvis_app.py
```

## 3. Manual UI checks

1. Open the Layouts/Presets dropdown.
2. Confirm Gaming, Coding, Music, and Minimal are gone.
3. Arrange panels into a layout you like.
4. Click Save Preset and give it a name.
5. Move panels around, then select the saved preset and confirm the saved layout comes back.
6. With the saved preset selected, click Rename and give it a new name.
7. Confirm the renamed preset still restores the same layout.
8. Select the preset and click Delete. Confirm deletion.
9. Confirm the preset disappears and the current panel positions do not jump.
10. Save several presets to verify there is no fixed built-in list or small preset cap.

## Success looks like

- Only user-created presets appear in the preset dropdown.
- Rename/Delete buttons are disabled until a custom preset is selected.
- Save/Rename/Delete dialogs are visible inside Jarvis.
- Existing panel drag, resize, maximize/restore, lock, and active-panel priority behavior still works.
