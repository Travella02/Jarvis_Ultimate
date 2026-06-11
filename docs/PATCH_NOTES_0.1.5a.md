# Jarvis Ultimate 0.1.5a — Sleep Phrase Robustness Hotfix

## Summary
0.1.5a fixes a real-world sleep/wake issue found during always-listening testing. Jarvis correctly woke from sleep mode and handled spoken commands, but if STT misheard the assistant name in a sleep phrase, such as hearing `That's all Dervis` instead of `That's all Jarvis`, Jarvis stayed awake.

This hotfix makes sleep phrase detection more tolerant while keeping wake detection strict enough to avoid accidental activation.

## Changes
- Added robust sleep phrase matching for sleep/wake voice mode.
- Allows common misheard Jarvis-name endings in sleep phrases, including `Dervis`, `Jervis`, `service`, `drivers`, and similar variants.
- Allows high-confidence sleep roots such as:
  - `that's all`
  - `that is all`
  - `that'll be all`
  - `go to sleep`
  - `go back to sleep`
  - `sleep mode`
  - `standby`
  - `stop listening`
- Adds sleep detection for polite assistant-targeted phrases like:
  - `thank you Jarvis`
  - `thanks Jervis`
  - `I'm done Jarvis`
- Preserves the existing exact phrase matching behavior.
- Adds tests for misheard sleep phrases and sleep/wake loop behavior.

## Why this matters
Jarvis is moving toward an always-listening assistant model. In that mode, failing to return to sleep when you say `that's all Jarvis` is disruptive because Jarvis may continue responding while you talk to other people. This hotfix prioritizes reliably going back to sleep when you use a clear sleep phrase.

## Notes
This is intentionally a small hotfix after 0.1.5. It does not add a new wake-word engine or barge-in. It only improves the sleep phrase state transition.
