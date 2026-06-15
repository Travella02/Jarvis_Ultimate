# Testing Guide — 0.2.6 App Agent Reliability + Launch Verification

## 1. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

No apps should open during the test suite.

## 2. Launch Jarvis

```powershell
python scripts\start_jarvis_app.py
```

## 3. Manual app tests

Try these with voice or the chat input:

```text
Jarvis, open Discord
Jarvis, close Discord
Jarvis, open calculator
Jarvis, close calculator
Jarvis, open Chrome
Jarvis, close Chrome
Jarvis, open VS Code
```

Jarvis should avoid saying an app opened unless the launch is accepted and the app process can be verified when a safe process name is known.

## 4. Manual alias learning tests

Try:

```text
Jarvis, when I say music, open Spotify
Jarvis, open music
```

Expected behavior:

- Jarvis should acknowledge the learned alias.
- The alias should be stored in `data/app_agent/app_aliases.json`.
- Future launches should use the learned alias faster.

## 5. Discord-specific check

If Discord previously failed after being closed, try:

```text
Jarvis, open Discord
```

The first attempt may take a little longer while Jarvis refreshes the launcher. Future attempts should be faster because the alias/path is relearned.
