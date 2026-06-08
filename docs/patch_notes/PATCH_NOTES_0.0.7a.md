# Patch Notes — 0.0.7a TTS Playback + XTTS Reference Setup

## Added

- `tts test play` command to generate and immediately play a test voice line.
- `tts play last` command to replay the most recently generated TTS WAV.
- `tts playback on` and `tts playback off` runtime commands.
- `tts reference` status command for the XTTS speaker WAV.
- `tts reference set <path>` to point XTTS at a reference WAV for the current runtime session.
- `tts reference import <path>` to copy a reference WAV into `assets/voices/jarvis_reference.wav`.
- `voice on` now enables both auto-speak and playback for the current CLI session.
- Cross-platform playback attempts:
  - Windows: `winsound`
  - macOS: `afplay`
  - Linux: `aplay`, `paplay`, or `ffplay` when available
- Additional tests for playback command flow, last-audio replay, and XTTS reference setup.

## Changed

- `tts status` now shows playback support and XTTS reference readiness.
- XTTS reference validation now requires a `.wav` path.
- The TTS manager tracks the active XTTS reference path at runtime so reference changes do not require restarting Jarvis.

## Notes

- The committed/default config still keeps playback off so Jarvis will not unexpectedly play audio on fresh installs.
- Use `tts test play`, `tts playback on`, or `voice on` when you want sound.
- XTTS v2 is still personal/non-commercial only in this project. Keep XTTS for Tanner's local Jarvis experiments, but swap to Kokoro, ElevenLabs, or another licensed provider before SaaS/commercial use.
