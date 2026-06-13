# Testing Guide — 0.2.5a Caption Live Sync Hotfix

## Automated tests

From the Jarvis project root, run:

```powershell
python -m unittest discover -s tests -v
```

Expected result: `OK`.

## Manual test

Launch Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

Try short app/tool commands:

```text
Jarvis, open calculator
Jarvis, close calculator
Jarvis, open notepad
Jarvis, close notepad
```

Expected behavior:

- Jarvis should still speak the response.
- The text under the orb should begin typing while Jarvis is speaking, not after he returns to listening.
- Short responses should type quickly enough to stay close to the spoken audio.
- The app shell should continue polling smoothly while voice mode is active.
