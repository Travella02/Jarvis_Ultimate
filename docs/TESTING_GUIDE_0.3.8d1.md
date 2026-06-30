# Testing Guide — 0.3.8d1 Secure Vault Version Test Alignment Hotfix

This hotfix only updates one test file that still expected the previous version number.

## 1. Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_8d1_secure_vault_version_test_hotfix.py
```

## 2. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

The previous failure in `tests/unit/test_memory_secure_vault_035a.py` should be gone.

## 3. Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

## 4. Manual check

There is no new manual UI behavior in this hotfix. After Jarvis starts, continue testing the `0.3.8d` Save Preset behavior:

- Arrange panels.
- Click `Save Preset`.
- Name the preset.
- Move panels or apply another layout.
- Select the saved custom preset again.
- Confirm the layout restores correctly.
