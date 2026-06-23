# Jarvis Ultimate 0.3.3a App Agent Test-Isolation Hotfix

Run the installer from the Jarvis project root:

```powershell
python apply_0_3_3a_app_agent_test_isolation_hotfix.py
```

Then run:

```powershell
python -m unittest discover -s tests -v
python scripts\start_jarvis_app.py
```

This patch only fixes App Agent launch-verification tests that could fail when Discord was already installed or running locally.
