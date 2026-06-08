# Patch Notes — 0.0.7c Kokoro Default TTS Cleanup

## Summary

0.0.7c moves Jarvis's active TTS path away from XTTS and makes Kokoro the default local provider.

XTTS is kept as an experimental personal/local provider only, but it is no longer part of the normal provider chain. This avoids the dependency issues found during testing and keeps the project cleaner for a possible SaaS future.

## Why this patch exists

XTTS testing exposed several environment-specific dependency problems:

- PyTorch CUDA visibility had to be fixed.
- Transformers versions caused import errors.
- NumPy 2.x caused binary compatibility errors.
- PyTorch checkpoint loading changed safety defaults.
- TorchCodec/FFmpeg became another dependency hurdle.

Kokoro already generated and played speech on Tanner's machine, so it is now the practical default.

## Changed

- Default TTS provider changed from `xtts` to `kokoro`.
- Default fallback chain changed from `kokoro,mock` to `mock`.
- Normal TTS no longer tries XTTS first.
- `tts status` now highlights Kokoro as the active local path.
- `tts voice list` now lists common Kokoro voice IDs when Kokoro is active.
- `tts voice use <voice_id>` switches Kokoro voices for the current runtime session.
- `tts voice current` shows the active Kokoro voice.
- `tts voice test <voice_id> play` tests a Kokoro voice directly when Kokoro is active.
- `tts say as <voice_id> <text>` speaks using that Kokoro voice when Kokoro is active.
- XTTS imports are now lazy so Kokoro installs do not import Coqui/TTS at boot.
- `requirements-tts.txt` is now Kokoro-focused for easier setup on desktop/laptop.
- Added `requirements-tts-xtts-experimental.txt` for optional later XTTS experiments.
- Installer updates the project `.env` TTS settings from XTTS to Kokoro where possible.

## Added

- `tests/unit/test_tts_kokoro_default.py`
- `tests/integration/test_runtime_kokoro_voice_flow.py`
- `docs/TESTING_GUIDE_0.0.7c.md`

## Notes

XTTS is still documented as experimental/personal-only. Do not use XTTS for a SaaS/commercial Jarvis unless a separate commercial license is obtained.

Kokoro is now the supported local TTS path for the current rebuild. ElevenLabs or another licensed provider can be added later through the same provider system.
