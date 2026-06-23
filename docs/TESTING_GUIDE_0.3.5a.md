# Testing Guide — Jarvis Ultimate 0.3.5a

Run these commands from the Jarvis project root.

## 1. Apply the patch

```powershell
python apply_0_3_5a_sensitive_memory_vault_routing_patch.py
```

## 2. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

The patch workspace passed with:

```text
Ran 405 tests in 5.385s
OK
```

## 3. Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

Or double-click:

```powershell
Start_Jarvis_Ultimate_App.bat
```

## 4. Manual checks

Ask Jarvis:

```text
Secure vault status.
```

Expected: Jarvis should say secure vault routing is ready, but encrypted vault storage is not enabled yet.

Then test a fake password:

```text
Remember that my password is hunter2.
```

Expected: Jarvis should not say he saved it to normal memory. He should explain that passwords cannot be saved in normal memory and encrypted local vault storage is not enabled yet.

Then test fake financial data:

```text
Remember that my bank account number is 123456789.
```

Expected: Jarvis should route it to the secure-vault path and not save it in normal memory.

Then verify normal memory still works:

```text
Remember that Jarvis patches should include the start command after tests.
What do you remember about Jarvis patches?
```

Expected: Normal non-sensitive project memory should continue working.
