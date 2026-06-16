# Testing Guide — 0.3.0b Memory Duplicate Filtering Hotfix

## Automated tests

Run from the Jarvis project root:

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

Try this flow:

```text
Jarvis, from now on, I prefer short direct patch instructions.
Jarvis, what memories are waiting for review?
Jarvis, save that permanently.
Jarvis, what do you remember about patch instructions?
```

Expected behavior:

- The review list should show the patch-instruction preference only once.
- Saving should say something like `I saved that permanently, sir.` instead of claiming multiple duplicate saves.
- Recall should say something like `I remember that you prefer short direct patch instructions, sir.` only once.
