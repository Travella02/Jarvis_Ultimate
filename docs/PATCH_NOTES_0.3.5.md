# Jarvis Ultimate 0.3.5 — Memory Preferences + Auto-Remember Controls

## Summary

This update adds a user-controlled memory preference layer so Jarvis can decide whether possible memories should be saved automatically, queued for review, kept temporarily, or ignored.

This is a SaaS-focused privacy foundation: different users and future tenants can decide what Jarvis is allowed to remember before deeper automation, screen awareness, and app/game setting capture are added.

## What changed

- Added `src/jarvis/memory/preferences.py`.
- Added crash-safe memory preference persistence at `data/memory/memory_preferences.json`.
- Added memory policies:
  - `auto` — save safe/useful memories automatically.
  - `ask` — queue the memory as a review candidate.
  - `short_term` — save as temporary fact memory.
  - `never` — do not save.
- Added default categories:
  - people
  - pets
  - relationships
  - projects
  - apps
  - app settings
  - game settings
  - screen context
  - devices
  - vehicles
  - places
  - work
  - preferences
  - daily life
  - health
  - financial
  - secrets
  - private
  - general
- Added Memory Agent commands for memory preferences:
  - `remember project rules automatically`
  - `ask me before remembering people`
  - `never remember financial information`
  - `keep daily life temporary`
  - `show my memory preferences`
  - `reset my memory preferences`
- Auto-capture now checks memory preferences before saving anything.
- Explicit memory commands now respect `never` and `short_term` policies.
- Secret-like data such as passwords, API keys, account/card numbers, SSNs, tokens, and private keys is not automatically stored.
- Added future-ready handling for `remember these settings` so screen/app/game settings can later be stored from real visual context instead of a vague note.
- App shell version updated to `0.3.5`.
- Added app-shell capabilities:
  - `memory_preferences_auto_remember_controls`
  - `memory_policy_privacy_controls`
  - `screen_setting_memory_policy_ready`

## Why this matters

Memory is becoming powerful enough that Jarvis needs policy controls before it becomes more automatic. This patch gives Jarvis safe defaults and user-controlled rules for SaaS-style privacy.

For the future screen-awareness workflow, this means a user can eventually say:

```text
Jarvis, remember these game settings.
```

Then the Screen Agent/OCR/Vision Agent can pass the visible settings into this same memory policy layer, and Jarvis can store them under `game_settings` or `app_settings` instead of saving an unhelpful vague sentence.

## Validation

Validated in the patch workspace with:

```powershell
PYTHONPATH=src python -m unittest discover -s tests -v
```

Result:

```text
Ran 397 tests in 5.600s

OK
```
