# Jarvis Ultimate 0.1.2 — Always-Ready Voice Runtime Cleanup

## Summary

0.1.2 improves the always-running voice experience before the continuous hands-free loop. It addresses three practical issues discovered during 0.1.1 testing:

1. Jarvis was keeping every generated TTS WAV file.
2. Smart listening felt a little slow because the default silence endpoint was conservative.
3. STT/TTS warmup was still manual, so first voice use could feel slower than later turns.

## Added

- Bounded TTS retention:
  - `JARVIS_TTS_MAX_OUTPUT_FILES=30`
  - `tts cleanup`
- Bounded STT/microphone recording retention:
  - `JARVIS_STT_MAX_AUDIO_FILES=30`
  - `stt cleanup`
- Combined cleanup command:
  - `audio cleanup`
- Always-ready warmup commands:
  - `warmup status`
  - `warmup all`
  - `tts warmup`
  - existing `stt warmup`
- Runtime listen responsiveness tuning:
  - `listen faster`
  - `listen balanced`
  - `listen safer`
  - `stt silence 0.8`
- TTS warmup helper that loads/generates once without playback and deletes the warmup output.
- STT/TTS retention details in status output.
- New tests for retention cleanup, warmup helpers, config loading, and CLI parsers.

## Changed

- Default smart listen silence stop changed from `1.0s` to `0.75s`.
- Default minimum record time changed from `0.35s` to `0.25s`.
- Default start timeout changed from `5.0s` to `4.0s`.

These defaults should make Jarvis stop listening sooner after you finish speaking while still leaving enough room to avoid cutting you off.

## Notes

Jarvis keeping audio files was expected in the earlier foundation versions because it made debugging easier. For an always-running assistant, unbounded audio output is not a good default, so 0.1.2 keeps only the latest configured number of TTS/STT WAV files.

LLM warmup is documented but skipped in 0.1.2 because LM Studio may not always be running at boot. We can add an optional safe LLM ping later.
