# Testing Guide — 0.1.7 Native App Shell Foundation

## 1. Run the full test suite
From the Jarvis Ultimate root with the venv active:

```powershell
python -m unittest discover -s tests -v
```

Success should show all tests passing.

## 2. Boot the normal Jarvis runtime
```powershell
python scripts/run_jarvis.py
```

Expected:

```text
Jarvis 3 is online. Registered 9 agents.
```

The exact registered-agent count can change later if agents are added or disabled.

## 3. Test the local app-shell API only
Open PowerShell in the project root and run:

```powershell
python scripts/start_local_api_server.py
```

Then open a second PowerShell window and run:

```powershell
python - <<'PY'
import json
from urllib.request import urlopen
print(json.loads(urlopen('http://127.0.0.1:8765/api/health').read().decode()))
print(json.loads(urlopen('http://127.0.0.1:8765/api/state').read().decode())['data']['avatar']['state'])
PY
```

Expected:
- `/api/health` returns `success: True`.
- `/api/state` returns a state snapshot with an `avatar`, `runtime`, `workspace`, and `app` section.

Press `Ctrl+C` in the API server window when finished.

## 4. First-time Electron setup
The Electron shell uses Node dependencies. First-time setup:

```powershell
cd app_shell
npm install
cd ..
```

This creates `app_shell/node_modules/` locally. Do not commit `node_modules`.

## 5. Start the new native app shell
After Electron dependencies are installed:

```powershell
python scripts/start_jarvis_app.py
```

Or double-click:

```text
Start_Jarvis_Ultimate_App.bat
```

Expected:
- A desktop app window opens named `Jarvis Ultimate`.
- It does not open as a normal browser tab.
- The orb appears in the center.
- The bridge badge should change to `Bridge Online`.
- Runtime information appears on the left.
- Workspace panels appear on the right.
- Typing `list agents` in the app shell sends a command through the local API and updates the conversation panel.

## 6. Fallback behavior
If you have not run `npm install` yet, this command:

```powershell
python scripts/start_jarvis_app.py
```

will explain the Electron setup step and then open the existing Tkinter Jarvis desktop body as a fallback. That is expected.

## 7. Existing desktop UI still works
```powershell
python scripts/start_jarvis.py
```

Expected:
- The previous Tkinter desktop body still opens.
- The solid orb renderer still works.

## 8. Commit only after success
If tests pass and the app shell opens correctly:

```powershell
Remove-Item apply_0_1_7_native_app_shell_patch.py
Remove-Item -Recurse patch_files

git add .
git commit -m "0.1.7 Add native app shell foundation"
git push
```
