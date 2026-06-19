# Jarvis Ultimate 0.3.1a — Humanized Entity Memory Responses Hotfix

This hotfix keeps the 0.3.1 scalable entity-memory foundation intact and improves how Jarvis talks about entity memories.

## Why this patch exists

The 0.3.1 entity memory store worked, but the responses were too database-like. For example, asking who someone is could return text like:

```text
Structured entity memories:
- Lee (person): Lee is the user's fiance.
```

That is technically correct storage output, but it does not feel like Jarvis. Jarvis should answer naturally, such as:

```text
Kenleigh is your fiancée, sir.
```

## Changes

- Added a humanized entity response path in Memory Agent.
- Entity search/list answers now prefer natural wording over raw structured-memory formatting.
- If an LLM provider is available, Memory Agent asks the local LLM to rewrite entity-memory answers into short, natural Jarvis-style responses.
- If the LLM is unavailable, Jarvis still uses deterministic natural fallback responses.
- The LLM humanizer is guarded so it only uses provided entity facts and does not invent details.
- Response wording now prefers second person:
  - `your fiancée` instead of `the user's fiancée`,
  - `your dog` instead of `the user's dog`,
  - `your project` instead of `the user's project`.
- Entity prompt context also converts stored summaries to second-person wording before being sent to the LLM.
- Relationship extraction now supports multi-word names like `Ken Lee is my fiance`.
- `fiance` and `fiancee` normalize to `fiancée`.
- Entity type normalization now supports plural type words such as `pets`, `people`, `projects`, `apps`, `places`, `devices`, `vehicles`, and `organizations`.
- This fixes list-style commands such as `list remembered pets` using the saved pet records.
- Added the app-shell capability flag `entity_memory_humanized_responses`.
- Updated app-shell version to `0.3.1a`.

## Important note

This patch does not yet add entity correction/merge commands. If STT hears `Kenleigh` as `Ken Lee`, Jarvis can now store and answer more naturally, but a future patch should add commands like:

```text
Jarvis, rename entity Ken Lee to Kenleigh.
Jarvis, merge Ken Lee with Kenleigh.
Jarvis, Ken Lee and Kenleigh are the same person.
```

## Files changed

- `src/jarvis/agents/memory_agent/agent.py`
- `src/jarvis/memory/entities.py`
- `src/jarvis/clients/app_shell/bridge.py`
- `tests/unit/test_memory_entity_humanized_031a.py`
- Updated app-shell version assertions in existing tests
- `README.md`
- `JARVIS_ULTIMATE_HANDOFF_INSTRUCTIONS.md`

## Validation

Validated with:

```powershell
PYTHONPATH=src python -m unittest discover -s tests -v
```

Result:

```text
Ran 353 tests in 3.190s
OK
```
