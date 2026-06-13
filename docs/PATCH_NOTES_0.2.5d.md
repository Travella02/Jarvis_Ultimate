# Jarvis Ultimate 0.2.5d — Live Caption Before TTS Hotfix

This hotfix fixes the remaining app-shell caption timing issue for short app/tool responses.

## Fixed

- Stages complete non-streamed app/tool replies before Jarvis waits on TTS playback.
- Fixes the issue where Jarvis would finish speaking, return to listening, and only then start typing the orb caption.
- Keeps the public app-shell version at `0.2.5` for this committed feature set.

## Why this was happening

LLM responses stream chunks while speaking, so the UI receives text early. App/tool responses are often one complete string. The previous hotfix staged the caption, but it happened after the spoken pipeline wait path, so very short responses could still finish audio before Electron saw the caption.
