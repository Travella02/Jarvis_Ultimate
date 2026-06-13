# Jarvis Ultimate 0.2.3 — Smart App Discovery + Voice Readback Hotfix

## Summary

This update improves the 0.3.0 ability framework by making the App Agent more useful and fixing voice readback for non-LLM agent/tool responses.

## Changes

- Added smart desktop app discovery for the App Agent.
- Added learned app alias storage at `data/app_agent/app_aliases.json`.
- Added cached app discovery index at `data/app_agent/app_index.json` so repeat app launches are faster.
- Added built-in app aliases such as:
  - `google` → Chrome
  - `google browser` → Chrome
  - `chrome` → Chrome
  - `code`, `vscode`, `visual studio code` → VS Code
  - `calc` → Calculator
- Added fuzzy matching against discovered apps and Start Menu shortcuts.
- Added close-app support for commands like:
  - `close chrome`
  - `quit notepad`
  - `exit calculator`
- Added safety guardrails so the close command avoids critical system processes.
- Updated the App Agent ability metadata to include close-app capability.
- Fixed spoken voice behavior so Jarvis reads non-LLM agent responses aloud, including app/file/tool responses.

## Notes

- First launch of an unknown app can take longer because Jarvis may scan common app locations.
- After Jarvis successfully opens or closes an app, he learns that alias so the next request is faster.
- Closing apps is best-effort and intentionally avoids force-closing critical system processes.
