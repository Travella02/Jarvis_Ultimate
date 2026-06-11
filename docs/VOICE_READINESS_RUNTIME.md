# Voice Readiness Runtime

Jarvis Ultimate is intended to eventually run all day. Voice systems therefore need to be bounded, warmable, and adjustable.

## Audio retention

Earlier TTS/STT foundation patches kept generated WAV files for debugging. 0.1.2 keeps only the most recent files:

```env
JARVIS_TTS_MAX_OUTPUT_FILES=30
JARVIS_STT_MAX_AUDIO_FILES=30
```

Manual cleanup commands:

```text
audio cleanup
tts cleanup
stt cleanup
```

## Warmup

Warmup loads voice subsystems before the first real voice turn:

```text
warmup status
warmup all
stt warmup
tts warmup
```

Optional boot warmup:

```env
JARVIS_VOICE_WARMUP_ON_BOOT=true
JARVIS_VOICE_WARMUP_STT=true
JARVIS_VOICE_WARMUP_TTS=true
JARVIS_VOICE_WARMUP_LLM=false
```

LLM warmup is intentionally skipped in 0.1.2 so Jarvis does not hang boot if LM Studio is not open.

## Endpointing responsiveness

Smart listening stops after speech ends plus the configured silence window:

```env
JARVIS_STT_SILENCE_SECONDS=0.75
```

Runtime tuning commands:

```text
listen faster
listen balanced
listen safer
stt silence 0.8
```

Lower values feel faster but can cut speech off. Higher values are safer but less responsive.
