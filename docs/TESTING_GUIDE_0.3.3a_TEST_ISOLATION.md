# Testing Guide — 0.3.3a App Agent Test-Isolation Hotfix

## Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_3a_app_agent_test_isolation_hotfix.py
```

## Run the test suite

```powershell
python -m unittest discover -s tests -v
```

Then start Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

Or double-click:

```powershell
Start_Jarvis_Ultimate_App.bat
```

## If imports fail

In the same PowerShell window, run:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
python scripts\start_jarvis_app.py
```

## Expected result

The two App Agent launch-verification failures should be gone:

- `test_verified_launch_waits_for_expected_process`
- `test_stale_launcher_retries_refreshed_real_app_path`

The full suite should end with `OK`.

## Manual checks

After Jarvis starts, test the 0.3.3a behavior that started this round:

```text
What do you remember about Kenleigh?
```

Jarvis should answer naturally, such as:

```text
Kenleigh is your fiancée, sir.
```

He should not say `structured entity memory`, and the orb should not rapidly flicker between speaking and sleeping during a typed response.
