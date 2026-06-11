# Patch Notes — 0.1.1 Wake Word Foundation

## Summary

0.1.1 adds Jarvis's first wake-word foundation without introducing another heavy dependency. This version uses phrase detection over the STT transcript, so Tanner can test commands such as `wake voice once` before Jarvis becomes fully always-on.

This is intentionally not a continuous background wake engine yet. It is the safe bridge between the 0.1.0 one-turn voice loop and the later always-running wake-word loop.

## Added

- Dependency-free wake-word manager.
- Configurable wake phrases:
  - `hey jarvis`
  - `jarvis`
- Wake-word config in `config/providers.yaml`.
- Wake-word config in `.env.example`.
- CLI commands:
  - `wake status`
  - `wake test Hey Jarvis, give me one sentence`
  - `wake listen once`
  - `wake voice once`
  - `wake loop smart max 8 silence 0.8`
- Runtime helpers:
  - `wake_status()`
  - `wake_test()`
  - `wake_listen_once()`
  - `wake_voice_once()`
- Wake events:
  - `wake_word.detected`
  - `wake_word.not_detected`
  - `wake_word.listen_started`
- Tests for wake detection, config loading, CLI parsing, and runtime wake voice flow.

## Behavior

`wake voice once` performs one microphone turn:

```text
listen
→ transcribe
→ check for wake word
→ remove wake phrase
→ send remaining command to Jarvis
→ speak response
```

Example:

```text
You say: Hey Jarvis, give me one short sentence.
Detected wake word: hey jarvis
Command sent to Jarvis: give me one short sentence
```

If Tanner only says `Hey Jarvis`, Jarvis responds with the configured empty-wake response:

```text
Yes, sir?
```

## Not Included Yet

- Continuous always-on wake-word listening.
- Porcupine/openWakeWord integration.
- Barge-in while Jarvis is speaking.
- Automatic follow-up listening after Jarvis speaks.

Those should come in later patches.

## Recommended Next Patch

0.1.2 should add a continuous hands-free conversation loop built on this wake-word foundation.
