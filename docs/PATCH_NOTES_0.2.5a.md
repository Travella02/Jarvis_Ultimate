# Jarvis Ultimate 0.2.5a — Caption Live Sync Hotfix

## What changed

- Stages short app/tool responses in the voice session before TTS playback begins.
- Adds a tiny pre-speech caption lead so Electron can poll the response before the audio finishes.
- Speeds active app-shell polling while Jarvis is listening, thinking, speaking, or holding a live response.
- Speeds up the short-response caption typewriter so commands like “Opening calculator, sir.” appear while Jarvis is speaking instead of after he is done.
- Updates app shell version to `0.2.5a`.

## Why

Short non-LLM tool responses do not stream token-by-token like normal LLM chat. They were being spoken so quickly that the UI often did not receive the response until after playback finished and Jarvis returned to listening mode.
