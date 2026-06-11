# Wake Word Foundation

Jarvis 0.1.1 adds the first wake-word layer. It is intentionally simple and dependency-free: Jarvis listens for one microphone turn, transcribes it with STT, then checks whether the transcript starts with a configured phrase such as `hey jarvis`.

## Current Mode

Current wake-word mode is phrase detection over STT text.

```text
microphone -> STT transcript -> phrase wake detector -> command after wake word -> Jarvis brain
```

This is not the final always-on wake engine. It is the foundation that later continuous listening will use.

## Default Wake Words

```text
hey jarvis
jarvis
```

## Commands

```text
wake status
wake test Hey Jarvis, give me one sentence
wake listen once
wake voice once
wake loop smart max 8 silence 0.8
```

`wake listen once` only reports whether the wake phrase was detected.

`wake voice once` detects the phrase and sends the command after it into Jarvis.

## Empty Wake Phrase

If Tanner says only `Hey Jarvis`, Jarvis responds with:

```text
Yes, sir?
```

This can be configured with:

```env
JARVIS_WAKE_EMPTY_RESPONSE="Yes, sir?"
```

## Configuration

```env
JARVIS_WAKE_WORD_ENABLED=true
JARVIS_WAKE_WORD_PROVIDER=phrase
JARVIS_WAKE_WORDS="hey jarvis,jarvis"
JARVIS_WAKE_REQUIRE_WAKE_WORD=true
JARVIS_WAKE_STRIP_WAKE_WORD=true
JARVIS_WAKE_EMPTY_RESPONSE="Yes, sir?"
```

## Future Work

The likely next versions are:

- 0.1.2 continuous hands-free conversation loop
- 0.1.3 barge-in / interrupt while Jarvis is speaking
- later: optional dedicated wake engine provider such as Porcupine or openWakeWord
