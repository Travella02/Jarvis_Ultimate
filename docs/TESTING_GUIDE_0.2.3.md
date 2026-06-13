# Testing Guide — 0.2.3 Smart App Discovery + Voice Readback

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

## 3. Test app opening

Try these commands by voice or typed chat:

```text
Jarvis, open notepad
Jarvis, open calculator
Jarvis, open chrome
Jarvis, open google
Jarvis, launch google browser
Jarvis, open VS Code
```

Expected result:

- Jarvis should open the app or say he could not find a matching app.
- Jarvis should read the response aloud, not only show it in text.
- Workspace action cards should appear for open/close actions.

## 4. Test learned aliases

Try opening an app using a nickname or partial name. If Jarvis finds and opens it, repeat the same command.

Expected result:

- The second attempt should be faster because Jarvis stores the alias/path in `data/app_agent/app_aliases.json`.

## 5. Test close app

Open Notepad, then say or type:

```text
Jarvis, close notepad
```

Expected result:

- Jarvis should attempt to close Notepad.
- Jarvis should read the response aloud.
- If the app is not running, Jarvis should explain that he found the app but does not see it running.

## 6. Safety check

Try:

```text
Jarvis, close system
```

Expected result:

- Jarvis should not close critical system processes.
