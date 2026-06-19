# Jarvis Ultimate 0.3.2 — Entity Merge + Alias Correction

This update adds explicit correction controls to the structured entity-memory system. The goal is to make Jarvis resilient to STT mistakes, duplicate names, nicknames, and early entity extraction errors without forcing the user to manually edit JSON memory files.

## What changed

- Added entity resolution that checks exact names and aliases before falling back to search scoring.
- Added entity merge support for commands like:
  - `Ken Lee and Kenleigh are the same person.`
  - `Nugget and Nuggie are the same dog.`
- Added entity rename support for commands like:
  - `Change Lee to Kenleigh.`
  - `Rename Ken Lee to Kenleigh.`
- Added entity alias support for commands like:
  - `Add Ken Lee as an alias for Kenleigh.`
  - `Ken Lee is another name for Kenleigh.`
  - `Call Kenleigh Ken.`
- Added entity alias removal support for commands like:
  - `Forget the alias Ken Lee, but keep Kenleigh.`
  - `Remove Ken Lee as an alias for Kenleigh.`
- Entity merges preserve useful details from both records: summaries, aliases, attributes, relationships, tags, confidence, importance, and metadata.
- Entity renames preserve the old name as an alias, so previous STT mistakes still resolve to the corrected entity.
- Memory Agent now handles entity edit actions before normal memory search/list/save handling.
- Intent classifier now routes entity correction commands to the Memory Agent instead of app control or general chat.
- App shell version is now `0.3.2`.
- App shell capabilities now include `entity_memory_merge_alias_correction`.

## Why this matters

Jarvis is voice-first, so names will sometimes be heard wrong. This update gives Jarvis a clean correction path instead of creating messy duplicate memories.

Example:

1. STT hears `Kenleigh` as `Ken Lee`.
2. Jarvis saves a person/entity memory under the wrong name.
3. You say: `Ken Lee and Kenleigh are the same person.`
4. Jarvis merges the records and keeps `Ken Lee` as an alias.
5. Later, `Who is Ken Lee?` still resolves correctly to `Kenleigh`.

## Files changed

- `src/jarvis/memory/entities.py`
- `src/jarvis/agents/memory_agent/agent.py`
- `src/jarvis/brain/intent_classifier.py`
- `src/jarvis/clients/app_shell/bridge.py`
- `tests/unit/test_memory_entity_alias_merge_032.py`
- Existing version assertion tests were updated to expect `0.3.2`.
- `JARVIS_ULTIMATE_HANDOFF_INSTRUCTIONS.md`
- `README.md`

## Test result

Validated in the patch workspace with:

```powershell
PYTHONPATH=src python -m unittest discover -s tests -v
```

Result:

```text
Ran 368 tests in 3.717s

OK
```

## Next recommended memory update

The best next memory update is either:

- `0.3.3 Relationship Memory Graph`, so Jarvis can reason over links between people, pets, projects, apps, devices, places, organizations, and the user.
- `0.3.3 Memory Preferences / Auto-Remember Controls`, so users can say what Jarvis may remember automatically, what should require approval, and what should never be saved.
