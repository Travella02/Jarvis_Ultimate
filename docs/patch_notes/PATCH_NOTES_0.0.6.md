# Patch Notes — 0.0.6 Short-Term Conversation Memory

## Summary

This update adds Jarvis's first real short-term conversation memory layer. Jarvis now keeps a bounded rolling window of recent user/assistant chat turns and injects that context into future LLM conversation turns so follow-up questions work more naturally.

This is **not** permanent long-term memory. It is session memory for recent conversation continuity.

## Why this matters

Jarvis is intended to eventually run for long periods, so short-term memory cannot grow forever. This patch is built around bounded memory limits from the start:

- maximum stored turns
- maximum stored characters
- maximum injected turns per LLM request
- optional autosave setting, disabled by default

This keeps Jarvis conversational without letting an always-running process slowly build an oversized prompt or memory object.

## Added

- `src/jarvis/memory/short_term.py`
  - `ShortTermMemory`
  - `ConversationTurn`
  - rolling turn storage
  - prompt-message conversion
  - trimming by turn count and character budget
  - status/last/clear helpers
  - optional autosave support

- Runtime integration
  - `JarvisRuntime` creates a `ShortTermMemory` instance during boot.
  - Successful `llm_chat` turns are saved after the response finishes.
  - Router passes short-term memory into agent context.
  - Conversation Agent injects recent turns before the current user message.

- CLI commands
  - `memory status`
  - `memory last`
  - `memory last 10`
  - `memory clear`

- Config settings
  - `JARVIS_MEMORY_SHORT_TERM_ENABLED=true`
  - `JARVIS_MEMORY_SHORT_TERM_MAX_TURNS=20`
  - `JARVIS_MEMORY_SHORT_TERM_MAX_CHARS=12000`
  - `JARVIS_MEMORY_SHORT_TERM_INJECT_LAST_TURNS=8`
  - `JARVIS_MEMORY_SHORT_TERM_AUTOSAVE=false`

- Diagnostics
  - `prompt stats` now reports short-term memory status.
  - `timing last` includes `conversation.memory_context_selected`.
  - Saved chat turns include `memory.short_term_turn_saved`.

## Changed

- Normal LLM chat requests now include recent session memory turns when available.
- CLI startup hint now includes memory commands.
- `config/providers.yaml` and `.env.example` now document the short-term memory settings.

## Important behavior notes

- Short-term memory only records successful normal LLM chat turns.
- It does not store diagnostic commands like `timing last`, `prompt stats`, or `benchmark llm`.
- It does not make Jarvis permanently remember personal facts yet.
- The Memory Agent is still mostly a placeholder for future long-term memory tools.
- Autosave is available but off by default. With autosave off, memory resets when Jarvis restarts.

## Tests added

- Short-term memory unit tests
- Conversation Agent memory injection tests
- Runtime memory recording tests
- Runtime memory clear tests
- Config loading tests for memory settings

## Test result from patch build

```text
Ran 63 tests
OK
```

Boot check:

```text
Jarvis 3 is online. Registered 9 agents.
```
