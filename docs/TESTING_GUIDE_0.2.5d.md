# Testing Guide — 0.2.5d

Run the full suite:

```powershell
python -m unittest discover -s tests -v
```

Expected result: OK.

Then launch Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

Manual check:

```text
Jarvis, open calculator
Jarvis, close calculator
Jarvis, open Chrome
Jarvis, close Chrome
```

The text under the orb should begin typing while Jarvis is speaking, not after the orb returns to listening.
