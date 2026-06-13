# Testing Guide — 0.2.4

## Automated tests

From the Jarvis project root, run:

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
Jarvis, can you pull up VS Code?
Jarvis, could you open Calculator?
```

Expected behavior:

- Snipping Tool should resolve faster than before.
- Known apps should usually open through fast aliases or cached paths.
- Jarvis should still speak/tool-read responses.
- During thinking, the orb should shift purple/violet.
- After startup, app indexing should happen in the background without blocking voice mode.
