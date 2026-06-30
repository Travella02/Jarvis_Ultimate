# Jarvis Ultimate 0.3.8d1 — Secure Vault Version Test Alignment Hotfix

This is a tiny follow-up hotfix for `0.3.8d — Save Custom Layout Preset`.

## What changed

- Updated `tests/unit/test_memory_secure_vault_035a.py` so the version assertion expects `0.3.8d` instead of the previous `0.3.8c4` checkpoint.
- No runtime behavior changed.
- No UI behavior changed.
- No app-shell version bump; the active Jarvis version remains `0.3.8d`.

## Why this was needed

The Save Custom Layout Preset patch correctly updated the app-shell runtime version to `0.3.8d`, but one older secure-vault test file was not included in the patch package and still expected `0.3.8c4`. That made the full test suite fail even though the actual runtime behavior was fine.

## Validation

Validated in the patch workspace with:

```powershell
node --check app_shell/renderer/renderer.js
python -m unittest discover -s tests -v
```

Result:

```text
Ran 450 tests in 3.618s

OK
```
