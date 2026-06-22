# Jarvis Ultimate 0.3.3 — Typed Input Voice Parity

## Purpose

This update fixes the interface behavior where typed commands went through a quieter app-shell path instead of feeling like normal Jarvis voice turns.

Typed commands are intentional input, so they should not need the wake word. But after submission, they should still behave like real Jarvis commands: route through the same runtime brain/agent pipeline, speak the response out loud, update the orb caption while speaking, and keep the microphone sleep/wake loop alive afterward.

## Changes

- `/api/command` now accepts typed commands with `speak=true` by default.
- Typed app-shell commands now use the same spoken response pipeline used by voice commands.
- Typed input does not require wake-word detection.
- Typed command responses stream into the orb caption while Jarvis speaks.
- Complete non-streamed tool/agent replies still get pre-speech caption staging, so short responses appear before/while TTS plays.
- Running sleep/wake voice sessions are preserved after typed commands.
- The voice session snapshot now tracks:
  - `typed_turns_handled`,
  - `last_input_mode`,
  - typed command response text.
- The Electron renderer now sends normal typed commands with `speak: true` and `input_mode: "typed"`.
- The desktop/Tk fallback typed input path now also uses spoken playback and returns to the voice-running state when voice runtime is active.
- App shell version is now `0.3.3`.
- Added capability flag: `typed_input_voice_parity`.

## Why this matters

This keeps Jarvis from feeling like two separate assistants: one voice Jarvis and one silent typed chat. Normal typed input now behaves like a deliberate Jarvis command, while voice input still uses wake-word protection to avoid accidental activations.

## Files changed

- `src/jarvis/api/local_server.py`
- `src/jarvis/clients/app_shell/bridge.py`
- `src/jarvis/clients/desktop/app.py`
- `app_shell/renderer/renderer.js`
- app-shell version assertion tests
- `tests/unit/test_app_shell_typed_voice_parity_033.py`
- `README.md`
- `JARVIS_ULTIMATE_HANDOFF_INSTRUCTIONS.md`

## Validation

Validated with:

```powershell
PYTHONPATH=src python -m unittest discover -s tests -v
```

Result:

```text
Ran 371 tests in 3.564s
OK
```
