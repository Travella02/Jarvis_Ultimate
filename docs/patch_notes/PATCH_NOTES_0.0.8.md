# Patch Notes — 0.0.8 Spoken Response Pipeline

## Summary

0.0.8 connects normal Jarvis chat to voice output. When voice mode is enabled,
Jarvis can stream text to the CLI while sentence chunks are sent to a background
TTS queue for speech.

## Added

- `SpokenResponsePipeline` background TTS queue.
- Sentence/soft-boundary TTS chunking helpers.
- Streaming callback adapter that prints LLM chunks and queues speech chunks.
- `voice status` for combined TTS + spoken queue diagnostics.
- `tts queue` / `tts queue status`.
- `tts stop`, `voice stop`, `stop speaking`, and `silence` commands.
- Best-effort `TTSManager.stop_playback()` support.
- New config values:
  - `JARVIS_TTS_AUTO_SPEAK_CHUNK_CHARS`
  - `JARVIS_TTS_QUEUE_MAX_SIZE`
- New unit/integration tests.

## Changed

- `voice on` now enables the spoken response queue path for normal chat instead
  of doing a blocking full-response TTS call after the LLM finishes.
- `voice off` disables auto-speak/playback and clears pending speech chunks.
- The CLI help text now includes voice pipeline commands.
- TTS generation results now include `tts_elapsed_ms` in result data.

## Design Notes

This patch keeps voice output outside Jarvis Brain. The brain still returns text
results. The CLI/body layer decides whether to speak those results, which keeps
future desktop UI/avatar/WebSocket clients clean and swappable.

The queue is bounded because Tanner plans for Jarvis to eventually be always
running. Jarvis should not accumulate unlimited speech chunks during long
sessions.

## Known Limits

- The background worker can clear pending chunks and stop Windows winsound
  playback, but it cannot interrupt every possible provider while it is still
  generating audio.
- This is output voice only. Microphone/STT input is still a future patch.
- Kokoro remains the default local TTS provider. XTTS remains experimental and
  non-commercial/personal-only.
