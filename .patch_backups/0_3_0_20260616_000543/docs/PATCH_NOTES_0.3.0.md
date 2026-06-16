# Jarvis Ultimate 0.3.0 — Ability Framework + Basic Computer Actions

This milestone moves Jarvis beyond UI-only polish and starts the real ability layer.

## Added

- New `jarvis.abilities` package with:
  - `AbilityRegistry`
  - `AbilityRecord`
  - command-to-ability selection metadata
  - basic risk/permission decisions
- Runtime now builds an ability registry from enabled agent manifests during boot.
- Router now includes selected ability metadata in route events/results.
- Router now emits result UI events so agents can create app-shell action cards.
- App shell runtime snapshot now exposes ability count and ability metadata.
- Workspace UI now has action cards for recent tool/ability actions.
- App Agent now has a real safe launcher ability for allowlisted apps/websites.
- File Agent now has safe read-only project status and filename search.
- File Agent write-style requests now return a confirmation-required result instead of doing anything dangerous.
- Conversation status/list-agents now reports registered abilities.

## Early real commands to try

- `Jarvis, open notepad`
- `Jarvis, open calculator`
- `Jarvis, open VS Code`
- `Jarvis, open the project folder`
- `Jarvis, open google`
- `Jarvis, project status`
- `Jarvis, search project files for renderer`
- `Jarvis, list agents`

## Notes

This update does **not** make every placeholder agent fully capable yet. It creates the framework so future agents can be added one by one without messy one-off routing.
