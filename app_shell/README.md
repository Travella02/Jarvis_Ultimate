# Jarvis Ultimate App Shell

This folder contains the first native desktop app shell for Jarvis Ultimate.

It uses:

- Electron for the desktop window
- HTML/CSS/JavaScript for the visual interface
- Jarvis's Python local API bridge for state and commands

## First-time setup

From the project root:

```powershell
cd app_shell
npm install
cd ..
python scripts\start_jarvis_app.py
```

After the Electron dependency is installed, `python scripts\start_jarvis_app.py` starts the local Python bridge and opens the Jarvis app shell as a desktop app, not a browser tab.

If Electron is not installed yet, the launcher falls back to the existing Tkinter desktop body so Jarvis still opens.
