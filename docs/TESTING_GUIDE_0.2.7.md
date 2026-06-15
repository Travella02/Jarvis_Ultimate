# Testing Guide — Jarvis Ultimate 0.2.7

## Automated tests

From the main Jarvis project folder, run:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

No real apps should open during the unit tests.

## Manual tests

Launch Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

Try these commands:

```text
Jarvis, when I say music or jams, open Spotify
Jarvis, open music
Jarvis, open jams
Jarvis, forget the nickname jams
Jarvis, open music
Jarvis, what app aliases do you remember?
```

Expected:
- `music` and `jams` both point to Spotify after learning.
- Forgetting `jams` removes only that alias.
- `music` should still work after `jams` is forgotten.

Try default app roles:

```text
Jarvis, use Microsoft Edge as my main browser
Jarvis, open browser
Jarvis, switch to browser
Jarvis, close browser
```

Expected:
- Jarvis should use Microsoft Edge for `browser` commands.
- If the app is already running, Jarvis should try to bring it forward instead of opening another copy.

Try alias rename:

```text
Jarvis, when I say music, open Spotify
Jarvis, rename music to jams
Jarvis, open jams
```

Expected:
- `jams` should now point to Spotify.
- `music` should be removed when using the explicit rename command.

## Commit command

After testing and cleanup:

```powershell
git add .
git commit -m "0.2.7 Add app alias management and default roles"
git push
```
