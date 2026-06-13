# Testing Guide — 0.2.3a Smart App Agent Hotfix

## 1. Run the full test suite

From the Jarvis project root:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## 2. Launch Jarvis

```powershell
python scripts\start_jarvis_app.py
```

Wait for the app shell to show the bridge online and voice warmup ready.

## 3. Test spoken app responses

Say these through sleep/wake mode:

```text
Jarvis, open calculator
Jarvis, close calculator
```

Expected result:

- Calculator opens.
- Jarvis speaks the response out loud, not just types it.
- Calculator closes or Jarvis gives a clear reason if Windows blocks it.

## 4. Test app discovery

Try:

```text
Jarvis, open Chrome
Jarvis, open Google Chrome
Jarvis, open VS Code
Jarvis, launch Google browser
```

Expected result:

- Jarvis should search discovered launchers instead of only relying on PATH.
- The first discovery may take a little longer.
- If found and opened, the alias should be learned for next time.
- If not found, Jarvis should say he could not find the app.

## 5. Check learned aliases

After a successful app open, check:

```text
data\app_agent\app_aliases.json
```

Expected result:

- The spoken alias should be stored there with the app path or launcher data.

## 6. Clean up temporary patch files before committing

```powershell
Remove-Item .\apply_0_2_3a_smart_app_agent_hotfix_patch.py -Force
Remove-Item .\patch_files -Recurse -Force
```
