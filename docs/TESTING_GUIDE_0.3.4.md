# Testing Guide — Jarvis Ultimate 0.3.4 Relationship Memory Graph

Run these commands from the Jarvis project root after applying the patch.

## 1. Apply the patch

```powershell
python apply_0_3_4_relationship_memory_graph_patch.py
```

## 2. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 380 tests
OK
```

The exact runtime can vary by machine.

## 3. Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

Or double-click:

```powershell
Start_Jarvis_Ultimate_App.bat
```

## 4. Manual memory checks

Try these typed or spoken commands:

```text
Remember that Kenleigh is my fiancée.
Who is my fiancée?
How is Kenleigh related to me?
```

Expected: Jarvis should answer naturally, like:

```text
Kenleigh is your fiancée, sir.
```

Then try:

```text
Remember that my dog Nugget is a golden doodle.
What dogs do I have?
What relationships do you remember?
```

Expected: Jarvis should mention Nugget naturally and should not say “structured entity memory,” “records,” or database-style wording.

Then try:

```text
Remember that Kenleigh works on Jarvis.
Who works on Jarvis?
```

Expected: Jarvis should mention that Kenleigh works on Jarvis.

## 5. What to watch for

Success looks like:

- Relationship questions route to the Memory Agent.
- Responses are conversational.
- Existing entity memory commands still work.
- Typed input still speaks responses out loud and does not break voice listening.
- Full unit tests pass.

Common issues:

- If imports fail, set `PYTHONPATH` for the current PowerShell session:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
python scripts\start_jarvis_app.py
```

- If Jarvis remembers duplicate names, use the existing 0.3.2 merge commands, such as:

```text
Ken Lee and Kenleigh are the same person.
```
