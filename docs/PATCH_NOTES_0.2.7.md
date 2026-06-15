# Jarvis Ultimate 0.2.7 — App Alias Management + Default Roles

## Added
- Multiple custom aliases per app.
  - Example: “Jarvis, when I say music or jams, open Spotify.”
- Default app roles.
  - Example: “Jarvis, use Microsoft Edge as my main browser.”
  - Then “open browser” uses the selected browser.
- Alias management commands.
  - List remembered aliases.
  - Forget aliases/nicknames/names/app names.
  - Rename aliases.
- Focus/switch support.
  - “Switch to Chrome,” “bring up VS Code,” and “focus Discord” route through App Agent.
  - Opening an app that is already running will try to bring it forward instead of launching another copy.
- App Agent capability metadata for alias management, default roles, and focus control.

## Improved
- Learned aliases and roles now take priority over built-in aliases and broad app discovery.
- The alias store is now more SaaS-ready: aliases and default roles are stored locally per project/device.
- App intent routing now recognizes more natural alias/default-app phrases.

## Safety
- Unit tests remain dry-run safe. App Agent tests should not open real apps.
- Focus support is best-effort and uses safe process names only.
