# Testing Guide — 0.3.0 Ability Framework

## 1. Run the automated tests

From the main Jarvis project folder:

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

Jarvis should open the Electron app shell and auto-enter sleep/wake if Auto Wake is on.

## 3. Test safe abilities

Try typing or speaking:

```text
Jarvis, list agents
Jarvis, project status
Jarvis, search project files for renderer
Jarvis, open notepad
Jarvis, open calculator
Jarvis, open the project folder
Jarvis, open google
```

## 4. What success should look like

- `list agents` should mention agents and abilities.
- `project status` should report source/app-shell/tests/agent info.
- `search project files for renderer` should return matching files.
- Open-app commands should either open the target app/website or tell you the launcher is not available on your machine.
- The Workspace panel should show recent ability action cards.

## 5. Safety check

Try:

```text
Jarvis, delete this file
```

Jarvis should require confirmation and should not delete anything.
