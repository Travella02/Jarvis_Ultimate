# Jarvis Ultimate 0.3.1 — Scalable Entity Memory Foundation

## Summary

0.3.1 adds a structured entity-memory layer beside the existing long-term memory, short-term facts, chat archive, and memory candidate queue. This lets Jarvis remember important "things" as first-class records instead of only storing plain text facts.

This is designed for the future SaaS version: entity types are registry-driven, records are JSON-backed, and new entity types can be added without changing the storage schema.

## Added

- New `jarvis.memory.entities` module.
- New crash-safe `EntityMemoryStore` at `data/memory/entities.json`.
- New scalable entity type registry with default entity types:
  - `user`
  - `person`
  - `pet`
  - `project`
  - `app`
  - `place`
  - `device`
  - `vehicle`
  - `organization`
- Entity records support:
  - name,
  - type,
  - aliases,
  - summary,
  - attributes,
  - relationships,
  - tags,
  - source,
  - confidence,
  - importance,
  - sensitivity,
  - scope,
  - metadata.
- `register_entity_type(...)` so future SaaS-specific types can be added without schema changes.
- Conservative entity inference for examples like:
  - `Kenleigh is my fiancée` → person entity,
  - `my dog Scout is a golden doodle` → pet entity,
  - `my car is a 2013 Ford Fusion Hybrid SE` → vehicle entity,
  - `my main music app is Spotify` → app entity,
  - Jarvis project/update/version statements → project entity.
- Secret guardrails: obvious passwords, API keys, payment cards, and SSN-like content are not converted into entity memory.
- Entity memory context injection into normal LLM conversation when relevant.
- Memory Agent support for entity list/search/status flows.
- Candidate approval can also promote inferred entity records when appropriate.
- Explicit `remember that...` memory saves can also update entity memory when the text contains an inferable entity.
- App shell snapshot now exposes entity-memory status.
- App shell capabilities now include:
  - `structured_entity_memory_foundation`,
  - `scalable_entity_type_registry`,
  - `entity_memory_context_injection`.
- New tests for 0.3.1 entity memory behavior.

## Config added

New `.env.example` options:

```powershell
JARVIS_MEMORY_ENTITY_ENABLED=true
JARVIS_MEMORY_ENTITY_PATH=data/memory/entities.json
JARVIS_MEMORY_ENTITY_MAX_RECORDS=2000
JARVIS_MEMORY_ENTITY_INJECT_LIMIT=5
```

## SaaS notes

This update intentionally keeps entity memory local-first and user-controlled, but the schema is ready for SaaS growth:

- `scope` can separate personal/workspace/team memories later.
- `metadata` can hold tenant/workspace IDs later.
- `sensitivity` gives future policy logic a place to decide whether an entity can be auto-saved, reviewed, exported, or deleted.
- Entity types can be added by registry rather than by hardcoding new classes.

Important SaaS entity categories to keep building toward:

- users/profiles,
- people/relationships/contacts,
- pets/care context,
- projects/products/repos,
- apps/tools/services,
- devices/hardware,
- vehicles,
- places,
- organizations/vendors/schools/banks,
- future routines/tasks/subscriptions/workspaces/customers.

## Changed

- `APP_SHELL_VERSION` is now `0.3.1`.
- Existing version tests were updated from `0.3.0` to `0.3.1`.
- Memory status now includes entity-memory status.
- Normal memory searches can include structured entity matches along with long-term and short-term memories.

## Validation

Validated in this patch workspace with:

```powershell
PYTHONPATH=src python -m unittest discover -s tests -v
```

Result:

```text
Ran 349 tests in 3.366s
OK
```

