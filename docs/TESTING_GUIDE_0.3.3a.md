# Testing Guide — Jarvis Ultimate 0.3.3a

Run this from the Jarvis project root after applying the patch:

```powershell
python -m unittest discover -s tests -v
python scripts\start_jarvis_app.py
```

If imports fail in a fresh PowerShell window, run:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
python scripts\start_jarvis_app.py
```

## Manual checks

1. Start the app shell and let sleep/wake mode run.
2. Type this into the chat box without saying the wake word:

```text
What do you remember about Kenleigh?
```

Expected: Jarvis should answer naturally, for example:

```text
Kenleigh is your fiancée, sir.
```

Jarvis should not say `structured entity memory`, `records`, or anything database-style.

3. While Jarvis is answering a typed command out loud, watch the orb state.

Expected: the orb should stay in a stable speaking/thinking flow and should not rapidly flicker between speaking and sleeping.

4. After the typed response finishes, say a normal voice command, such as:

```text
Hey Jarvis, who is Kenleigh?
```

Expected: voice should still work. Typed input should not stop the sleep/wake voice loop.
