# Jarvis Ultimate 0.0.9b — STT GPU Acceleration

## Summary
0.0.9b makes Jarvis's local STT path GPU-aware so microphone transcription can feel fast enough for a real voice loop.

## Added
- `JARVIS_STT_DEVICE=auto` support.
- `JARVIS_STT_COMPUTE_TYPE=auto` support.
- CUDA-first faster-whisper mode when GPU is detected.
- CPU fallback when CUDA model loading/transcription fails.
- `stt gpu status` CLI command.
- `stt warmup` CLI command to pre-load the STT model before talking.
- STT status now reports CUDA diagnostics.
- Debug output now shows actual device, compute type, elapsed milliseconds, and fallback usage.
- `requirements-stt-gpu.txt` helper file for GPU setup notes.

## Changed
- Default STT config moved from CPU/int8 to auto/auto.
- `auto` uses `float16` on CUDA and `int8` on CPU.
- `providers.yaml` and `.env.example` now recommend GPU-aware STT settings.

## Notes
faster-whisper uses CTranslate2 for inference, not PyTorch. PyTorch CUDA detection is useful for diagnostics, but CTranslate2 may still need CUDA/cuBLAS/cuDNN runtime libraries on Windows before GPU inference works.

## Testing
Validated with:

```powershell
python -m unittest discover -s tests -v
```

Result in clean patched repo:

```text
Ran 107 tests
OK
```
