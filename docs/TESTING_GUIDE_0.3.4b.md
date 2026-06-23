# Testing Guide — Jarvis Ultimate 0.3.4b

Run these commands from the Jarvis project root after applying the patch.

## 1. Unit tests

```powershell
python -m unittest discover -s tests -v
```

If imports fail in PowerShell, run:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

## 2. Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

Or double-click:

```powershell
Start_Jarvis_Ultimate_App.bat
```

## 3. Manual memory checks

Try these in the Jarvis interface:

```text
Who is Ken Lee?
Who is Kenleigh?
Who is my fiance?
```

Expected behavior:

- Jarvis should resolve `Ken Lee` to `Kenleigh` if that alias exists.
- Jarvis should say `Kenleigh is your fiancée, sir.` naturally.
- Jarvis should not show brackets, lists, quotes, or raw structured memory wording.

Bad output that should be gone:

```text
Kenleigh is your ['fiance fiancee', 'fiancée'], sir.
```
