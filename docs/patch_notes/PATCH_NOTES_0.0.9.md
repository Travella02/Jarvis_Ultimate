# Jarvis Ultimate 0.0.9 — STT / Microphone Input Foundation

## Summary

0.0.9 adds the first speech-to-text input foundation for Jarvis Ultimate. It does not create the full always-listening voice loop yet. Instead, it gives Jarvis a clean, swappable STT provider system, microphone recording helper, one-shot listening commands, audio-file transcription commands, and diagnostics.

This keeps the architecture aligned with the existing provider pattern:

User microphone/audio file → STT Manager → STT Provider → Standard STT Result → CLI/runtime command handling

## Added

- `providers/stt/base.py`
- `providers/stt/manager.py`
- `providers/stt/factory.py`
- `providers/stt/audio_recorder.py`
- `providers/stt/mock_provider.py`
- `providers/stt/faster_whisper_provider.py`
- `providers/stt/whisper_provider.py` compatibility wrapper
- STT config fields in `JarvisConfig`
- STT section in `config/providers.yaml`
- STT settings in `.env.example`
- `requirements-stt.txt`
- Runtime helpers:
  - `stt_status()`
  - `stt_providers()`
  - `stt_record()`
  - `stt_listen_once()`
  - `stt_transcribe_file(path)`
  - `stt_debug_last()`
- CLI commands:
  - `stt status`
  - `stt providers`
  - `stt record`
  - `listen once`
  - `stt transcribe <path>`
  - `stt debug last`
- Tests for STT config, providers, microphone recorder formatting, and runtime flow.

## Provider defaults

The default STT provider is now:

```env
JARVIS_STT_PROVIDER=faster_whisper
JARVIS_STT_FALLBACK_PROVIDERS=mock
```

`faster_whisper` is the intended local/offline STT path. `mock` keeps Jarvis bootable and testable when STT dependencies, microphone access, or model downloads are not ready yet.

## Desktop/laptop setup note

To set this up on another machine, use:

```powershell
python -m pip install -r requirements-stt.txt
```

The default STT device is CPU/int8 for easier setup:

```env
JARVIS_STT_DEVICE=cpu
JARVIS_STT_COMPUTE_TYPE=int8
```

Later, GPU STT can be tested by switching to CUDA once the faster-whisper/CTranslate2 GPU dependencies are verified on that machine.

## Always-running note

This is intentionally a one-shot microphone foundation, not an always-listening loop. The next voice milestone should add a controlled loop with stop commands, wake/sleep states, echo protection, TTS/STT coordination, and safeguards so Jarvis does not listen forever without clear user control.

## Test result

Verified against the patched project with:

```powershell
python -m unittest discover -s tests -v
```

Result:

```text
Ran 102 tests
OK
```
