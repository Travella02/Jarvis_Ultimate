# Jarvis Ultimate 0.3.1c Testing Guide

## 1. Apply the patch

From the Jarvis Ultimate project root, run:

```powershell
python apply_0_3_1c_entity_forget_routing_patch.py
```

## 2. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

If imports fail in PowerShell, run:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## 3. Restart Jarvis

Fully close Jarvis and restart the app shell:

```powershell
python scripts\start_jarvis_app.py
```

Or double-click:

```text
Start_Jarvis_Ultimate_App.bat
```

## 4. Manual memory test

Use this exact sequence:

```text
Who is Scout?
Forget Scout.
List remembered pets.
```

Expected behavior:

- `Forget Scout.` should route to the Memory Agent.
- Jarvis should say he forgot the matching memory or memories.
- `List remembered pets.` should not include Scout anymore.
- Nugget should still appear if Nugget is still saved.

## 5. Extra routing test

Try one of these:

```text
Stop remembering Scout.
Delete memory Scout.
Do not remember Scout.
```

Expected behavior:

- Jarvis should not merely say a generic conversational response.
- The command should actually remove matching saved memory records.

## 6. What a failure means

If Jarvis says something like `Understood, I removed that information` but the entity still appears afterward, the command is still reaching conversation fallback instead of the Memory Agent. Re-run the tests and make sure the app was restarted after patching.
