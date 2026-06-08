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

## 0.0.9b GPU STT acceleration

Jarvis now supports GPU-aware faster-whisper configuration.

Recommended settings:

```env
JARVIS_STT_DEVICE=auto
JARVIS_STT_COMPUTE_TYPE=auto
JARVIS_STT_GPU_FALLBACK_TO_CPU=true
JARVIS_STT_DEVICE_INDEX=0
JARVIS_STT_WARMUP_ON_BOOT=false
```

Behavior:

- `device=auto` chooses CUDA when Jarvis detects a usable NVIDIA GPU, otherwise CPU.
- `compute_type=auto` becomes `float16` on CUDA and `int8` on CPU.
- `JARVIS_STT_GPU_FALLBACK_TO_CPU=true` keeps Jarvis usable if CUDA/CTranslate2 fails.
- `stt warmup` loads the model before voice testing so the first real spoken request does not pay the full model-load cost.

Useful commands:

```text
stt status
stt gpu status
stt warmup
listen once
stt debug last
```

Important: faster-whisper uses CTranslate2 for inference, not PyTorch. `torch.cuda.is_available()` can prove the NVIDIA driver/PyTorch CUDA path works, but CTranslate2 GPU inference may still require CUDA/cuBLAS/cuDNN runtime DLLs on Windows. If `stt warmup` or `listen once` falls back to CPU, run `stt debug last` and check the CUDA error message.
