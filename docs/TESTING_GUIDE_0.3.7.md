# Testing Guide — Jarvis Ultimate 0.3.7

## Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_7_memory_review_panel_patch.py
```

## Run the unit test suite

```powershell
python -m unittest discover -s tests -v
```

If imports fail, run:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

## Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

Or double-click:

```powershell
Start_Jarvis_Ultimate_App.bat
```

## Manual checks

Try saving a normal person/entity memory if one is not already present:

```text
Remember that Kenleigh is my fiancée.
```

Then try:

```text
Show everything you remember about Kenleigh.
```

Expected result:

- Jarvis should say a short response like: `Here is everything I know about Kenleigh, sir.`
- Jarvis should not speak a long list out loud.
- The Workspace panel should show a Memory Review card/panel with ranked bullet items.
- The most important facts, like relationships, should appear higher than lower-level aliases or temporary notes.

Then try:

```text
Speak everything you remember about Kenleigh.
```

Expected result:

- Jarvis should read the ranked memory review out loud because you explicitly asked him to speak it.

## Security check

Try only fake sensitive values:

```text
Remember that my password is Hunter 2.
Show everything you remember about password.
```

Expected result:

- Sensitive values should remain redacted or absent from normal memory review output.
- Passwords and financial details should not be exposed in the Memory Review panel.

## Common issues

If the Memory Review card does not appear, refresh the app shell once or restart Jarvis. The backend should still return the short spoken confirmation, but the UI needs the updated renderer files to show the ranked card surface.
