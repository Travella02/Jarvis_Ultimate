# Testing Guide — 0.3.0a Memory Candidate Response Humanization Hotfix

## Automated tests

Run the full test suite from the project root:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## Manual checks

Launch Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

Try:

```text
Jarvis, from now on, I prefer short direct patch instructions.
Jarvis, what memories are waiting for review?
Jarvis, save that permanently.
Jarvis, what do you remember about patch instructions?
```

Expected behavior:

- Candidate review should sound conversational.
- It should say `you prefer...`, not `I prefer...`, when referring to the user's preference.
- It should not expose raw confidence scores in normal speech.
- Recall should not say `From now on...` as part of the saved fact.

A good response is similar to:

```text
I found one possible memory waiting for review, sir: you prefer short direct patch instructions. I would treat that as a permanent memory.
```

And after saving:

```text
I remember that you prefer short direct patch instructions, sir.
```
