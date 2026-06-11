# Patch Notes — 0.1.0 Real Voice Loop

## Summary

0.1.0 connects the working STT, LLM streaming, memory, and TTS systems into one complete spoken turn.

Jarvis can now:

```text
listen once
→ transcribe what Tanner said
→ route the transcript through Jarvis Brain
→ stream the LLM response
→ speak the response through Kokoro/TTS
```

This is still command-triggered. Wake word is not included yet.

## Added

- `voice loop once`
- `talk once`
- `voice chat once`
- `conversation once`
- `listen and respond`
- `voice loop status`
- Tunable one-turn commands:
  - `voice loop smart max 8 silence 0.8`
  - `voice loop fixed 2`
- `JarvisRuntime.voice_loop_once()`
- `JarvisRuntime.voice_loop_status()`
- Voice loop events:
  - `voice.loop_started`
  - `voice.loop_transcript_ready`
  - `voice.loop_finished`
  - `voice.loop_failed`
- Tests for runtime voice loop and CLI parsing.

## Design

0.1.0 keeps the flow modular:

- STT remains a provider/manager concern.
- Jarvis Brain remains the routing decision maker.
- TTS remains provider-backed through the spoken response queue.
- CLI is only a client that triggers the reusable runtime method.

## Wake word status

Wake word is not implemented yet. The next recommended patch is `0.1.1 Wake Word Trigger Foundation`, which should reuse `voice_loop_once()` after a wake trigger is detected.
