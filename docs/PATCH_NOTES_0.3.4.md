# Jarvis Ultimate 0.3.4 — Relationship Memory Graph

## What changed

This update adds the first relationship graph layer to Jarvis entity memory.

Jarvis can now treat entities as connected things instead of isolated records. People, pets, projects, apps, devices, vehicles, places, organizations, and future SaaS-specific entity types can be connected through relationship edges.

## New capabilities

- Relationship graph helpers inside `EntityMemoryStore`.
- Queryable relationship edges with source entity, relationship type, target, scope, confidence, and raw metadata.
- Relationship lookup by relation type, such as fiancée, dog, cat, pet, project, or works on.
- Natural Memory Agent responses for relationship questions.
- Intent routing for relationship questions so they go to memory instead of general chat.
- Inference upgrades so people, pets, and Jarvis/project memories produce graph edges.
- Cross-entity relationship inference for simple project/work phrases like “Kenleigh works on Jarvis.”
- App shell version bumped to `0.3.4`.
- Capability flags added:
  - `relationship_memory_graph`
  - `relationship_memory_queries`
  - `saas_ready_entity_relationship_edges`

## Example commands

```text
Who is my fiancée?
How is Kenleigh related to me?
What dogs do I have?
What relationships do you remember?
Who works on Jarvis?
```

## SaaS design note

The relationship layer is intentionally generic. It does not hardcode only Tanner-specific people or pets. The same graph shape can later support workspaces, teams, customers, tickets, subscriptions, devices, projects, organizations, and tenant-scoped memories.

## Files changed

- `src/jarvis/memory/entities.py`
- `src/jarvis/agents/memory_agent/agent.py`
- `src/jarvis/brain/intent_classifier.py`
- `src/jarvis/clients/app_shell/bridge.py`
- Version assertion tests updated to `0.3.4`
- New tests: `tests/unit/test_memory_relationship_graph_034.py`
- Updated handoff file
