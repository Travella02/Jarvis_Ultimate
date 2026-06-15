# Testing Guide — 0.2.7a

## Automated test
Run from the project root:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## Manual check
Launch Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

Try:

```text
Jarvis, when I say music or jams, open Spotify
Jarvis, open music
Jarvis, open jams
Jarvis, what app aliases do you remember?
```

The alias behavior should stay the same as 0.2.7.
