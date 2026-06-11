# Jarvis Ultimate Voice Loop System

Version 0.1.0 adds the first complete spoken turn pipeline:

```text
microphone listen
→ speech-to-text transcription
→ Jarvis Brain / Router
→ LLM streaming response
→ spoken response queue
→ Kokoro TTS playback
```

This is intentionally a **one-turn voice loop**. It is not wake word yet and it is not an always-open conversation loop yet. It proves the full path safely before Jarvis starts listening continuously.

## Commands

```text
voice loop status
voice loop once
talk once
voice chat once
conversation once
listen and respond
voice loop smart max 8 silence 0.8
voice loop fixed 2
```

`voice loop once` uses the configured STT endpointing settings. By default, that means smart listening: Jarvis starts recording, waits for speech, and stops shortly after silence is detected.

## Recommended workflow

Start Jarvis:

```powershell
python scripts/run_cli.py
```

Warm the STT model first:

```text
stt warmup
```

Check settings:

```text
voice loop status
stt listen settings
tts status
```

Run one full spoken turn:

```text
voice loop once
```

Jarvis should print what he heard, stream the text response, and speak the response through the spoken response queue.

## Tuning latency

The most important setting is the silence cutoff:

```text
voice loop smart max 8 silence 0.8
voice loop smart max 8 silence 1.0
voice loop smart max 8 silence 1.2
```

Lower values feel faster, but may cut off natural pauses. Higher values are safer, but slower.

## Wake word status

Wake word is not implemented in 0.1.0. The next likely step is a wake-word/watch loop that triggers this exact one-turn path.

Suggested next versions:

```text
0.1.1 = wake-word detection / always-listening trigger foundation
0.1.2 = continuous hands-free conversation loop
0.1.3 = barge-in / stop speaking when Tanner starts talking
```

## Always-running design note

The voice loop is built through `JarvisRuntime`, `STTManager`, `JarvisRouter`, and `SpokenResponsePipeline` rather than hardwiring voice logic into the CLI. That keeps the path reusable for a future desktop UI, avatar, or background service.
