# Jarvis Ultimate 0.1.3 — Continuous Hands-Free Voice Loop

## Summary

0.1.3 adds the first continuous hands-free conversation loop. Jarvis can now keep listening across multiple spoken turns from the CLI instead of requiring `wake voice once` every time.

This is still a safe CLI-controlled/blocking foundation, not a detached always-on background daemon yet. You start it manually, stop it with a spoken stop phrase or Ctrl+C, and can limit max turns for testing.

## Added

- `handsfree start`
- `wake loop start`
- `voice loop continuous`
- `conversation start`
- Optional `max <n>` turn limits
- Optional `silence <seconds>` endpointing override
- Optional `no wake` mode for controlled no-wake conversation testing
- Continuous loop status output
- Spoken stop phrases:
  - `stop listening`
  - `stop conversation`
  - `stop voice loop`
  - `stop handsfree`
  - `go to sleep`
  - `goodbye jarvis`
  - `exit voice mode`

## Behavior

Default continuous mode requires a wake phrase each turn:

```text
handsfree start max 5
```

Then speak:

```text
Hey Jarvis, give me one short sentence.
Hey Jarvis, what did I just ask you?
Hey Jarvis, stop listening.
```

For no-wake testing:

```text
conversation start max 3
```

Then speak normal turns without saying the wake phrase each time.

## Safety notes

- The loop is blocking in the CLI so it cannot accidentally run hidden in the background.
- The default requires the wake word each turn.
- The loop has a max-turn limit.
- Jarvis waits for queued TTS speech to finish before listening again to reduce the chance of hearing his own voice.

## Not implemented yet

- True wake-word engine running continuously in the background.
- Barge-in / interrupting Jarvis while he is speaking.
- Background service mode.
- Full duplex conversation.

Those should come after this foundation is stable.
