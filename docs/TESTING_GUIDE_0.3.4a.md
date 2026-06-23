# Testing Guide — Jarvis Ultimate 0.3.4a

## 1. Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_4a_entity_phonetic_relationship_hotfix.py
```

## 2. Run the full unit test suite

```powershell
python -m unittest discover -s tests -v
```

If imports fail in a fresh PowerShell window, run:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

## 3. Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

Or double-click:

```powershell
Start_Jarvis_Ultimate_App.bat
```

## 4. Manual memory checks

Try these exact commands in the Jarvis interface:

```text
Remember that Kenleigh is my fiance.
Who is my fiancé?
Who is Ken Lee?
Ken Lee and Kenleigh are the same person.
Who is Ken Lee?
Who is Kenleigh?
```

## Expected results

Jarvis should answer naturally. Good examples:

```text
Kenleigh is your fiancée, sir.
```

or:

```text
Kenleigh is your fiancée, sir. I can also recognize Ken Lee as an alias.
```

Jarvis should not say:

```text
I do not have anyone saved as your fiancé yet, sir.
```

unless Kenleigh has truly not been saved.

## Notes

This patch does not make STT itself hear `Kenleigh` perfectly. Instead, it makes memory robust when STT hears `Ken Lee`, `Kenley`, or similar variants. A future dedicated STT custom vocabulary/name-bias update can improve transcription before it reaches memory.
