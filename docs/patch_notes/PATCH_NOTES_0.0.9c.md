# Patch Notes — 0.0.9c Low-Latency Listen Mode

## Summary

0.0.9c improves microphone responsiveness without requiring GPU STT. Instead of always recording a fixed 4-second clip, Jarvis can now listen until it detects speech has ended, then immediately transcribe.

## Added

- Smart microphone endpointing with silence stop detection.
- Configurable silence stop duration.
- Configurable max listen duration, start timeout, energy threshold, pre-roll, and frame size.
- `stt listen settings` command.
- `listen smart` command.
- `listen smart max 8 silence 0.8` one-off tuning command.
- `listen fixed 2` command for strict timer testing.
- Recording/debug output now shows listen mode and stop reason.
- Tests for smart endpointing, fixed listen override, parser behavior, and record formatting.

## Changed

- STT defaults are moved back to CPU/int8 for stable local operation.
- Default fixed recording duration is lowered from 4.0 seconds to 2.0 seconds.
- `listen once` now uses smart endpointing by default.

## Why

The previous CPU STT path worked, but the fixed 4-second recording window made Jarvis feel slow. The debug timing showed the recording duration was a bigger user-perceived delay than the CPU transcription time. Silence-based endpointing should make voice interaction feel much closer to real time while staying dependency-light.

## Notes

This is still not a full always-listening wake-word loop. It is a safer foundation for the next voice milestone:

```text
listen once
→ transcribe
→ send transcript to Jarvis Brain
→ stream response
→ speak response
```
