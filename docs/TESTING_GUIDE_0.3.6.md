# Jarvis Ultimate 0.3.6 Testing Guide

## 1. Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_6_sensitive_chat_redaction_patch.py
```

The installer copies the updated files and runs a one-time redaction cleanup over existing local memory/chat/log files.

## 2. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Expected result: all tests pass.

If imports fail, run:

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

## 4. Manual security checks

Try these with fake test values only:

```text
Remember that my password is Hunter 2.
Remember that my bank account number is 123456789.
Secure vault status.
```

Expected behavior:

- Jarvis should not save those values to normal memory.
- Jarvis should explain that secure vault routing is ready but encrypted vault storage is not enabled yet.
- The app-shell chat panel should show redacted values rather than raw secrets.
- Chat archive/log files should not contain the raw fake password or fake bank number.

## 5. Check local files manually

Look inside these folders if they exist:

```text
data/memory/chat_archive
logs
```

Search for your fake test values. They should not appear raw. You should see redacted placeholders instead.

## 6. Commit after validation

Delete the patch installer and `patch_files` folder before committing:

```powershell
del apply_0_3_6_sensitive_chat_redaction_patch.py
rmdir /s /q patch_files
```

Then run:

```powershell
git status
```

Do not commit runtime/private folders like:

```text
.env
data/memory/
data/chat_archive/
logs/
.venv/
__pycache__/
```
