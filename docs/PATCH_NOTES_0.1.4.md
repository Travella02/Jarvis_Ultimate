# Jarvis Ultimate 0.1.4 — Sleep/Wake Always-Listening Conversation Mode

## Summary

This patch adds the first sleep/wake conversation state machine for Jarvis voice mode. It is designed around the long-term always-running goal:

- Jarvis listens while asleep, but only responds when a wake phrase is detected.
- Wake phrases include `hey jarvis`, `jarvis`, `yo jarvis`, `okay jarvis`, and `ok jarvis`.
- After wake activation, Jarvis stays awake for continuous conversation without requiring the wake word every turn.
- Jarvis returns to sleep when a sleep phrase is spoken, such as `that's all Jarvis`, `that is all Jarvis`, or `go to sleep`.
- Jarvis can also return to sleep after an inactivity timeout, defaulting to 45 seconds.

## New commands

- `sleep wake status`
- `sleep wake start`
- `sleep wake start max 10 timeout 45`
- `always listening start`
- `always listening start max 10 timeout 30 silence 0.65`
- `sleep mode start`

## Behavior model

The new mode is separate from the older 0.1.3 continuous loop.

Older 0.1.3 wake loop:

```text
wake required every turn
Hey Jarvis, do this
Hey Jarvis, do that
Hey Jarvis, stop listening
```

New 0.1.4 sleep/wake loop:

```text
sleeping
Hey Jarvis, do this
awake
Do that too
What about this?
That's all Jarvis
sleeping again
```

## New config

`.env.example` and `config/providers.yaml` now document:

```env
JARVIS_WAKE_WORDS="hey jarvis,jarvis,yo jarvis,okay jarvis,ok jarvis"
JARVIS_VOICE_SLEEP_TIMEOUT_SECONDS=45
JARVIS_VOICE_SLEEP_PHRASES="that's all jarvis,thats all jarvis,that is all jarvis,that will be all jarvis,that'll be all jarvis,go to sleep,sleep mode,stop listening"
JARVIS_VOICE_EXIT_PHRASES="exit voice mode,stop handsfree,stop voice loop,goodbye jarvis,shut down voice loop"
```

## Notes

This is still a CLI/blocking foundation. It is not yet a true background service that runs silently behind the UI. That future service should use this state machine behavior as the foundation.

## Tests

Added unit tests for sleep/wake command parsing, config loading, wake activation, follow-up commands without wake word, sleep phrase handling, and inactivity timeout back to sleep.
