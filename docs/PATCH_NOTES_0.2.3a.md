# Jarvis Ultimate 0.2.3a — Smart App Agent Hotfix

## What changed

- Fixed app-shell sleep/wake voice so Jarvis reads tool/agent responses out loud instead of only typing them.
- Improved app opening so built-in aliases like Chrome and VS Code prefer real discovered launchers before generic PATH commands.
- Added a forced app-index refresh when the cached app index misses a target.
- Added more Windows app discovery sources:
  - Start Menu shortcuts
  - common executable paths
  - PATH executables
  - Windows `Get-StartApps` AppIDs for Microsoft Store/UWP apps
- Improved learned alias behavior by refreshing stale app discovery cache with a new index version.
- Improved close-app behavior for Windows apps such as Calculator.
- Added safer known process names for Chrome, Edge, VS Code, Calculator, Notepad, Terminal, and PowerShell.
- Updated app shell package version to `0.2.3a`.

## Why

The previous smart app agent could open Calculator, but it could not reliably find Chrome/VS Code when they were not available through PATH, and it could not close Calculator because Windows Calculator does not behave like a simple `calc.exe` process. Also, app-shell sleep/wake mode was displaying non-LLM agent results without always sending them through TTS.

## Notes

The first unknown app lookup may still take longer because Jarvis refreshes the app index. After a successful launch, Jarvis saves the alias and path in `data/app_agent/app_aliases.json` so future launches are faster.
