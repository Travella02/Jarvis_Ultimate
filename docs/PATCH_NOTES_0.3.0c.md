# Patch Notes — 0.3.0c Local API Disconnect Guard Hotfix

## Summary

This is a small stability hotfix for the native app-shell local API bridge.

Electron sometimes cancels or replaces frequent polling requests while the Python bridge is still writing a JSON response. On Windows, that can show up as terminal tracebacks like:

```text
ConnectionAbortedError: [WinError 10053] An established connection was aborted by the software in your host machine
```

That is usually a normal client disconnect, not a Jarvis runtime failure. This hotfix suppresses those expected disconnect errors while keeping real API failures visible.

## Changed

- Added local API disconnect detection for:
  - `ConnectionAbortedError`
  - `BrokenPipeError`
  - `ConnectionResetError`
  - common Windows/socket disconnect error codes
- Wrapped local API response writes so canceled UI polling requests do not fill the terminal with traceback noise.
- Added unit tests for disconnect classification.
- Updated `JARVIS_ULTIMATE_HANDOFF_INSTRUCTIONS.md`.

## Not changed

- No voice/STT behavior changes.
- No memory behavior changes.
- No app-agent behavior changes.
- No UI layout changes.

## Version note

This is a hotfix for the uncommitted `0.3.0` memory auto-capture work. The visible app-shell version remains `0.3.0` so existing version tests stay stable.
