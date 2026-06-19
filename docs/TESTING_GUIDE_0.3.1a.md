# Jarvis Ultimate 0.3.1a Testing Guide — Humanized Entity Memory Responses

## 1. Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_1a_entity_memory_humanized_responses_patch.py
```

The installer copies the replacement files into the project and creates backups under:

```text
.patch_backups/0.3.1a_entity_memory_humanized_responses/
```

## 2. Run the automated tests

Run:

```powershell
python -m unittest discover -s tests -v
```

If imports fail in a fresh PowerShell window, run:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

The patch workspace passed with:

```text
Ran 353 tests in 3.190s
OK
```

## 3. Manual Jarvis checks

Start Jarvis with the app shell:

```powershell
python scripts\start_jarvis_app.py
```

Or double-click:

```text
Start_Jarvis_Ultimate_App.bat
```

Then try these commands:

```text
Jarvis, remember that Kenleigh is my fiancée.
Who is Kenleigh?
```

Expected behavior:

```text
Kenleigh is your fiancée, sir.
```

Jarvis should not say:

```text
Structured entity memories:
- Kenleigh (person): Kenleigh is the user's fiancée.
```

Now test a pet memory:

```text
Remember that my dog Nugget is a golden doodle.
List remembered pets.
```

Expected behavior:

Jarvis should mention Nugget naturally and should not say he has no pet records.

## 4. STT mishear check

Try this text command to simulate what can happen when speech-to-text hears `Kenleigh` as two words:

```text
Remember that Ken Lee is my fiance.
Who is Ken Lee?
```

Expected behavior:

```text
Ken Lee is your fiancée, sir.
```

This does not fully solve name correction yet. A future update should add rename/merge commands so you can say:

```text
Jarvis, Ken Lee and Kenleigh are the same person.
```

## 5. What success looks like

- Entity memory status still works.
- Explicit memory saves still work.
- Entity answers sound conversational.
- Jarvis uses `your` wording instead of `the user's` wording.
- `list remembered pets` finds saved pet records.
- The full unit test suite passes.
