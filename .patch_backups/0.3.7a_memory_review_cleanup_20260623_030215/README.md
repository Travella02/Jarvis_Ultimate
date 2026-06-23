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

## Latest milestone: 0.3.7 Memory Review Panel

Jarvis can now show a ranked visual review of what he remembers about a person, pet, project, app, place, or topic. For visual review requests, Jarvis keeps the spoken response short and opens a Memory Review card/panel with bullet points ranked from most important to least important.

Example:

```text
Show everything you remember about Kenleigh.
```

Jarvis should say:

```text
Here is everything I know about Kenleigh, sir.
```

The detailed list appears in the workspace panel instead of being spoken aloud. To make Jarvis read the full list, ask:

```text
Speak everything you remember about Kenleigh.
```
