# Jarvis Ultimate 0.3.8d2 Testing Guide

## Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_8d2_save_preset_name_dialog_hotfix.py
```

## Run automated tests

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

## Manual checks

1. Open Jarvis and wait for the app shell to load.
2. Click **Save Preset**.
3. Confirm a visible dialog opens asking you to name the layout.
4. Type a name like `My Testing Layout`.
5. Click **Save Preset** or press **Enter**.
6. Open the Layouts dropdown and confirm the preset appears under **Custom**.
7. Move panels around.
8. Select your custom preset from the Layouts dropdown.
9. Confirm the layout returns to the saved position.
10. Click **Save Preset** again, then press **Escape** or **Cancel** and confirm no unwanted preset is saved.

## Success looks like

- The Save Preset button always opens a visible naming dialog.
- You can name the preset before saving.
- The preset appears under the Custom group.
- Selecting the preset restores the saved layout.
- Cancel/Escape/backdrop click closes the dialog without saving.
- Existing panel movement, maximize/restore scaling, and active-panel priority still work.

## Common issue

If the Layouts dropdown still shows an older saved preset from previous testing, that means the old localStorage value is still present. That is okay. Save a new preset with a new name and test that the new name appears under Custom.
