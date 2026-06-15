# Jarvis Ultimate 0.2.8 - Memory Pipeline Foundation

## Summary
Adds the first real long-term memory pipeline so Jarvis can explicitly save, search, list, and forget durable memories while keeping short-term session memory separate.

## Added
- Local JSON-backed `LongTermMemoryStore` at `data/memory/long_term_memory.json` by default.
- Real Memory Agent implementation for:
  - `remember that ...`
  - `what do you remember?`
  - `what do you remember about ...?`
  - `memory status`
  - `forget that ...`
- Long-term memory config options:
  - `JARVIS_MEMORY_LONG_TERM_ENABLED`
  - `JARVIS_MEMORY_LONG_TERM_MAX_RECORDS`
  - `JARVIS_MEMORY_LONG_TERM_INJECT_LIMIT`
  - `JARVIS_MEMORY_LONG_TERM_PATH`
- Relevant saved memories are injected into the LLM system prompt when useful.
- Memory abilities are now registered in the ability registry.
- App shell runtime snapshot includes memory status.
- Project handoff file is now part of the project and should be updated with every patch.

## Changed
- App shell version updated to `0.2.8`.
- Conversation responses now report `long_term_memories_used` in result data.
- `memory status` now reports both short-term and long-term memory.

## Safety Notes
- Jarvis only saves long-term memory when explicitly asked to remember/save/store/note something.
- Clearing all long-term memory requires confirmation.
- Long-term memory is local-first and stored as editable JSON for now.

## Next Recommended Step
After testing the memory pipeline, move to `0.3.0 File Agent Foundation` so Jarvis can find, open, and summarize files/folders safely.
