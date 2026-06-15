# Testing Guide - 0.2.8a Memory Response Humanization Hotfix

## Automated Tests
From the project root, run:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## Manual Voice/UI Tests
Launch Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

Try these commands:

```text
Jarvis, remember that my favorite test color is blue
Jarvis, what do you remember about my favorite test color?
Jarvis, memory status
Jarvis, forget the memory about favorite test color
```

## Success Criteria
- Jarvis should respond naturally when recalling memories.
- The memory search response should sound like: `I remember that your favorite test color is blue, sir.`
- Jarvis should not say `Saved memories matching ...` for normal user-facing memory recall.
- Memory status should remain readable and still include `Long-term memory status`.
- Tests should pass.
