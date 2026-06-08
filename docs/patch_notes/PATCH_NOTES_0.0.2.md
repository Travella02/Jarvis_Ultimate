# Jarvis Ultimate 0.0.2 Patch Notes

## Version
0.0.2 — Core Boot + Agent Registry + Event System

## What this adds

- Standard `JarvisResult` object for every future agent/tool response.
- Standard `JarvisEvent` object for UI/avatar/logging/event communication.
- Synchronous `EventBus` with event history and wildcard subscriptions.
- `AgentRegistry` that discovers agents from `src/jarvis/agents/*/manifest.py`.
- `JarvisRouter` that classifies commands and routes them to the right agent.
- Deterministic intent classifier for early trigger words and fallback chat.
- `JarvisRuntime` lifecycle boot system.
- Working CLI loop through `python scripts/run_cli.py`.
- New `conversation_agent` for normal chat fallback, status, and listing agents.
- Placeholder implementations for screen, app, voice, avatar, memory, file, recorder, and weather agents.
- Avatar state model for future UI/body reactions.
- JSONL runtime logging under `logs/brain/`.
- Real unit/integration tests for the new foundation.

## What this does not add yet

- Real local LLM conversation.
- Real Ollama/Qwen provider.
- Real screen OCR.
- Real app launching.
- Real voice/TTS/STT.
- Real desktop UI/avatar animation.

Those come after this foundation is stable.
