# Patch Notes — 0.0.7b XTTS Multi-Voice Profiles + TTS Debugging

## Summary

0.0.7b improves the Jarvis Ultimate TTS foundation by making XTTS voice references multi-profile instead of single-file only, and by exposing the exact reason XTTS fails before the system falls back to Kokoro or mock.

This patch also updates the conversation persona so Jarvis addresses Tanner as **sir** instead of using his name during normal conversation.

## Added

- Named XTTS voice profiles stored under:
  - `data/tts/voices/<voice_name>/reference.wav`
- New CLI commands:
  - `tts voice list`
  - `tts voice current`
  - `tts voice import <name> <path>`
  - `tts voice use <name>`
  - `tts voice test <name>`
  - `tts voice test <name> play`
  - `tts say as <name> <text>`
  - `tts voice delete <name>`
  - `tts xtts test`
  - `tts xtts test play`
  - `tts debug last`
- Direct XTTS testing with fallback disabled so XTTS errors are visible.
- Provider attempt tracking for the last TTS request.
- Better XTTS error capture including exception type and traceback snippet.
- Voice reference validation warnings for short, stereo, low-sample-rate, or unusual WAV files.
- New config value:
  - `JARVIS_TTS_VOICE_PROFILES_DIR=data/tts/voices`
- Tests for multi-voice profiles and CLI parsing.

## Changed

- `tts test` now says “Hello sir” instead of “Hello Tanner.”
- Conversation system prompts now instruct Jarvis to address Tanner as “sir.”
- TTS status now shows the active voice profile and voice profiles directory.
- Normal TTS still keeps fallback behavior, but `tts debug last` now reveals what failed before fallback.

## Important XTTS note

XTTS v2 remains configured for personal/local testing only. Do not use XTTS v2 in a future SaaS/commercial Jarvis build unless you have a separate commercial license or replace it with a licensed provider such as Kokoro, ElevenLabs, or another production-safe voice backend.

## Expected tests

```powershell
python -m unittest discover -s tests -v
```

Expected result from clean test setup:

```text
Ran 83 tests
OK
```
