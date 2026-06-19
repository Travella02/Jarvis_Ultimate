# Jarvis Ultimate 0.3.1b — Entity Forget Cleanup + Stale Response Guard

This is a small hotfix for the 0.3.1 entity memory foundation and the 0.3.1a humanized entity responses.

## Why this patch exists

Manual testing showed Jarvis could say he removed Scout from memory, but then `List remembered pets` could still mention Scout afterward.

That should never happen. If Jarvis confirms an entity was forgotten, entity list/search responses should not show that entity again unless the user saves it again.

## Changes

- Strengthened `EntityMemoryStore.forget()` so it removes all matching entity records by:
  - exact name,
  - alias,
  - source text,
  - summary/search blob,
  - token match.
- Added duplicate cleanup for loaded entity records sharing names or aliases.
- Added a stale-name guard around LLM-humanized entity responses.
- If the local LLM tries to mention a proper-name entity that was not in the selected memory results, Jarvis falls back to the deterministic safe response.
- Added tests for forgetting Scout, listing pets afterward, and blocking a stale LLM response that tries to reintroduce Scout.
- Updated app shell version to `0.3.1b`.
- Added capability flag: `entity_memory_forget_cleanup_guard`.

## Files changed

- `src/jarvis/memory/entities.py`
- `src/jarvis/agents/memory_agent/agent.py`
- `src/jarvis/clients/app_shell/bridge.py`
- `tests/unit/test_memory_entity_forget_cleanup_031b.py`
- Version assertion test files updated to `0.3.1b`
- `JARVIS_ULTIMATE_HANDOFF_INSTRUCTIONS.md`

## Validation performed

```powershell
PYTHONPATH=src python -m unittest discover -s tests -v
```

Result:

```text
Ran 357 tests in 4.999s
OK
```
