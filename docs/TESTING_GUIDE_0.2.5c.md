# Testing Guide — 0.2.5c

Run the full suite:

```powershell
python -m unittest discover -s tests -v
```

Expected result: OK.

Then launch Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

Manually check short app responses such as:

```text
Jarvis, open calculator
Jarvis, close calculator
```

The text under the orb should begin while Jarvis is speaking, not after he returns to listening.
