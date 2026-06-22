# Jarvis Ultimate 0.3.3a — Typed Input Stabilization + Natural Memory Search

This hotfix should be applied before committing 0.3.3. It keeps the typed-input voice parity update and fixes the two issues found during manual testing.

## Fixed

- `What do you remember about Kenleigh?` no longer returns database-style wording such as `structured entity memory`.
- Combined memory search now uses the same natural entity response layer as direct questions like `Who is Kenleigh?`.
- When an LLM provider is available, Jarvis can rewrite memory-search replies into short conversational answers while preserving deterministic fallback behavior.
- Person and pet entity names are displayed more naturally when STT or text input stored the name in lower case.
- Typed-command responses now hold the visible speaking/thinking state while the sleep/wake microphone loop continues in the background.
- Background sleep/wake visual updates are suppressed during typed playback so the orb should not rapidly flicker between speaking and sleeping.

## Version / capability

- App shell version: `0.3.3a`
- New capabilities:
  - `typed_input_visual_hold`
  - `humanized_memory_search_responses`

## Safety / behavior notes

- This does not stop the sleep/wake voice thread.
- This does not disable microphone listening.
- It only prevents background sleep/wake status updates from overriding the typed-command speaking state while Jarvis is actively handling a typed turn.
