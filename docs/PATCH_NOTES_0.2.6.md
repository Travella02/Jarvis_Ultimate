# Jarvis Ultimate 0.2.6 — App Agent Reliability + Launch Verification

## What changed

- Added verified app launches for Windows desktop apps.
- Jarvis now waits briefly for the expected process to appear before confidently saying an app opened.
- Added stale launcher fallback recovery for apps like Discord that may resolve through `Update.exe` or an outdated learned path.
- Added manual alias teaching for app names.
- Added app-shell capabilities for verified launches, verified closes, manual alias learning, and stale launcher fallback recovery.
- Bumped the app discovery cache version so stale launcher data is rebuilt.
- Kept tests safe: unit tests should not open real apps.

## New examples

```text
Jarvis, open Discord
Jarvis, close Discord
Jarvis, when I say music, open Spotify
Jarvis, when I say editor, open VS Code
```

## Notes

If Jarvis finds a launcher but cannot verify the app actually started, he should no longer falsely claim it opened. He should either retry a refreshed launcher or tell you he could not verify the launch.
