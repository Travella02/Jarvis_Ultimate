# Testing Guide — 0.2.5

## Automated tests
Run from the Jarvis project root:

```powershell
python -m unittest discover -s tests -v
```

Expected result: `OK`.

## Manual app discovery tests
Launch Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

Try:

```text
Jarvis, open Discord
Jarvis, close Discord
Jarvis, open Spotify
Jarvis, open Chrome
Jarvis, close Chrome
Jarvis, open VS Code
Jarvis, open Snipping Tool
```

Expected behavior:
- Jarvis should open known apps quickly.
- If Jarvis has to index apps, future attempts should be faster.
- Discord should prefer a real `Discord.exe` launcher when available.
- Closing apps should still use the protected taskkill behavior from 0.2.3e.

## Caption sync test
Ask Jarvis short app commands such as:

```text
Jarvis, open calculator
Jarvis, close calculator
```

Expected behavior:
- Jarvis should start typing the caption much closer to when he speaks.
- The caption should no longer wait until after short spoken responses finish.
