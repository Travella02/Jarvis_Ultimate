# Testing Guide — 0.2.4a

## Automated tests

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

No real apps should open during the test suite.

## Manual checks

Launch Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

Try:

```text
Jarvis, open Snipping Tool
Jarvis, close Snipping Tool
Jarvis, open Chrome
Jarvis, close Chrome
Jarvis, open VS Code
Jarvis, open Discord
Jarvis, open Spotify
```

Expected behavior:

- Known apps should open quickly.
- Snipping Tool should not take around a minute anymore after the fast path or learned alias exists.
- Apps exposed in Start Menu, registry App Paths, PATH, desktop shortcuts, or WindowsApps should resolve faster than a deep Program Files scan.
- If Jarvis cannot find an app, he should say so instead of hanging silently.
