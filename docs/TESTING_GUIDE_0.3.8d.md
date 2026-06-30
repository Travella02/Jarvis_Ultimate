# Testing Guide — Jarvis Ultimate 0.3.8d

## Automated tests

From the Jarvis project root, run:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

Then start Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

## Manual checks

1. Open Jarvis and confirm the top controls include **Save Preset** beside the layout selector.
2. Arrange panels into a layout you want to keep.
3. Click **Save Preset**.
4. Enter a clear name, such as `Main Work Layout`.
5. Open the **Layouts** dropdown and confirm the saved preset appears under **Custom**.
6. Move panels around or apply a built-in preset.
7. Select your custom preset and confirm the saved layout returns.
8. Maximize and restore Jarvis, then apply the custom preset again.
9. Confirm the preset scales into the workspace area and does not cover the top Jarvis control bar.
10. Drag the Core Orb panel and confirm the Conversation panel does not move by itself.

## Success looks like

- The custom preset is selectable after saving.
- Applying the custom preset restores the saved panel arrangement.
- Applying the preset after maximize/restore keeps panels inside the workspace area.
- Existing Lock, Min, Dock, Pop, Reset Layout, and built-in preset behavior still works.
- Moving one panel still does not move other panels.

## Common issues

- If an old saved layout looks strange, click **Reset Layout** once and create a fresh custom preset.
- If a preset name already exists, Jarvis should ask before replacing it.
- Custom presets are local to this app/browser storage. Clearing Electron/Chromium app data can remove them.
