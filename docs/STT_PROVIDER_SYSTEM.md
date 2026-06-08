# Jarvis STT Provider System

Jarvis STT is designed to stay swappable. The brain should not know whether speech is coming from faster-whisper, another local engine, a cloud API, or a future wake-word pipeline.

## Current providers

### faster_whisper

The preferred local/offline provider for 0.0.9.

Config:

```env
JARVIS_STT_PROVIDER=faster_whisper
JARVIS_STT_MODEL=base.en
JARVIS_STT_DEVICE=cpu
JARVIS_STT_COMPUTE_TYPE=int8
```

CPU/int8 is the default because it is the easiest laptop/desktop setup. CUDA can be tested later after faster-whisper/CTranslate2 GPU dependencies are verified.

### mock

Dependency-free fallback used by tests and fresh installs.

## Current commands

```text
stt status
stt providers
stt record
listen once
stt transcribe <path>
stt debug last
```

## Intended future flow

0.0.9 only records/transcribes one command at a time. The next voice milestone should coordinate:

```text
microphone input
→ STT transcript
→ Jarvis Brain / Router
→ streamed LLM response
→ spoken response queue
→ TTS playback
```

The always-running version should add wake/sleep state, echo cancellation/ducking, stop commands, and safeguards before enabling continuous listening.
