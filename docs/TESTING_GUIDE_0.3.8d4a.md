# Testing Guide — Jarvis Ultimate 0.3.8d4a

## Apply

Run from the Jarvis project root after copying this installer and `patch_files` into the root:

```powershell
python apply_0_3_8d4a_preset_visibility_installer_fix_patch.py
```

## Automated tests

```powershell
python -m unittest discover -s tests -v
```

## Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

## Manual checks

1. Save one custom preset with only two panels open.
2. Save another custom preset with more panels open.
3. Switch between the presets.
4. Confirm each preset opens the panels it saved and closes the panels it did not save.
5. Confirm Rename and Delete still work.
