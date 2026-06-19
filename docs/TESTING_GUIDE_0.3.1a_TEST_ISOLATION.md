# Jarvis Ultimate 0.3.1a Test Isolation Hotfix — Testing Guide

## Apply the hotfix

From the Jarvis Ultimate project root, run:

```powershell
python apply_0_3_1a_test_isolation_hotfix.py
```

## Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

If imports fail in PowerShell, run:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

## Expected result

The previous failure should be gone:

```text
FAIL: test_router_passes_entity_memory_to_memory_agent
AssertionError: 4 != 1
```

The full suite should finish with:

```text
OK
```

## Manual Jarvis check

This hotfix does not change runtime memory behavior, but you can still confirm entity memory works:

```text
Jarvis, remember that my dog Nugget is a golden doodle.
Jarvis, list remembered pets.
```

Jarvis should answer naturally and include Nugget.
