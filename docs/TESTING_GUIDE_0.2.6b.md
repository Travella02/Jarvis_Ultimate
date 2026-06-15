# Testing Guide — 0.2.6b

## Automated tests

From the project root, run:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

No real apps should open during the unit tests.

## Manual checks

Launch Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

Then try:

```text
Jarvis, when I say music, open Spotify
Jarvis, open music
Jarvis, close music
```

Expected behavior:

- The alias-teaching phrase should not go to normal conversation.
- Jarvis should acknowledge that he learned the alias.
- `open music` should use Spotify after the alias is learned.
- If Spotify is running, `close music` should try to close Spotify.

## UI scroll check

Open the conversation panel, scroll upward in the chat history, and wait for Jarvis/app state refreshes. The chat should no longer keep snapping back to the newest message while you are reading older messages.
