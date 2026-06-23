# Testing Guide — Jarvis Ultimate 0.3.5

## 1. Apply the patch

From the Jarvis Ultimate project root, run:

```powershell
python apply_0_3_5_memory_preferences_patch.py
```

## 2. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

If imports fail in a fresh PowerShell session, run:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

Expected result: all tests pass. The patch workspace passed with `Ran 397 tests ... OK`.

## 3. Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

Or double-click:

```powershell
Start_Jarvis_Ultimate_App.bat
```

## 4. Manual memory-preference checks

Try these in Jarvis:

```text
Show my memory preferences.
```

Expected: Jarvis explains what he remembers automatically, what he asks about, what he keeps temporary, and what he will not save.

```text
Remember project rules automatically.
```

Expected: Jarvis confirms he will remember project rules automatically.

```text
Ask me before remembering people.
```

Expected: Jarvis confirms he will ask before saving people memories.

```text
Never remember financial information.
```

Expected: Jarvis confirms he will not save financial information.

```text
Reset my memory preferences.
```

Expected: Jarvis returns to the safe defaults.

## 5. Explicit memory checks

Set daily life to temporary:

```text
Keep daily life temporary.
Remember that today I ate pancakes.
```

Expected: Jarvis saves that as temporary memory, not permanent memory.

Set financial information to never:

```text
Never remember financial information.
Remember that my bank balance is a test value.
```

Expected: Jarvis should say he did not save it because memory preferences say not to remember financial information.

## 6. Future screen-settings check

Try:

```text
Jarvis, remember these settings.
```

Expected right now: Jarvis should not save a vague memory. He should explain that once screen awareness can pass him the settings, he can remember visible app/game settings.

This confirms the future screen/app/game settings path is policy-ready without pretending Jarvis can already see those settings in this update.
