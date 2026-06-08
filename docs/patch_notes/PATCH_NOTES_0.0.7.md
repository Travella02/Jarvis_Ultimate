# Patch Notes — 0.0.7 TTS Provider Foundation

## Goal

Add a clean, swappable text-to-speech foundation for Jarvis without hardwiring
voice generation into the brain or CLI.

## Added

- New TTS provider interface and result objects.
- New `TTSManager` for provider selection, fallback, output files, and optional
  WAV playback.
- Optional `xtts` provider for Tanner's current personal/local Jarvis voice
  experiments.
- Optional `kokoro` provider as the local fallback and SaaS-safer direction.
- Dependency-free `mock` provider for tests and fresh installs.
- CLI commands:
  - `tts status`
  - `tts providers`
  - `tts test`
  - `tts say <text>`
  - `voice on`
  - `voice off`
- New config/env settings for TTS provider selection, GPU preference, reference
  voice WAV path, fallback providers, output directory, playback, and auto speak.
- Optional `requirements-tts.txt`.
- `docs/TTS_PROVIDER_SYSTEM.md`.
- SaaS licensing note warning that XTTS v2 must be swapped before commercial or
  SaaS use unless a commercial license is secured.
- Tests for TTS config, provider fallback, mock synthesis, runtime helpers, and
  CLI parsing.

## Not added yet

- Streaming sentence-by-sentence TTS during LLM generation.
- Microphone input/STT.
- Wake word.
- ElevenLabs provider.
- Voice profile manager UI.

## Notes

This patch intentionally keeps heavy TTS dependencies optional. Jarvis should
boot and the full test suite should pass even if XTTS/Kokoro are not installed.
