# Patch Notes — 0.1.2a Smart Listen Endpointing Hotfix

## Goal
Fix smart listening sessions that keep recording until the maximum listen duration even after Tanner stops speaking.

## Why this patch exists
0.1.2 made Jarvis more responsive by lowering the silence stop time, but one real microphone test still recorded nearly the full max duration for a short phrase. That usually means the microphone/background noise stayed above the fixed RMS energy threshold, so Jarvis never detected silence.

## Changes
- Adds adaptive smart-listen energy thresholding.
- Adds a short ambient calibration window before speech detection.
- Adds endpointing debug details:
  - effective energy threshold
  - peak RMS
  - adaptive energy enabled/disabled
- Lowers default smart-listen latency settings:
  - max listen: 6.0 seconds
  - silence stop: 0.65 seconds
  - min record: 0.20 seconds
  - start timeout: 3.0 seconds
- Adds runtime tuning commands:
  - `stt energy 0.03`
  - `stt adaptive on`
  - `stt adaptive off`
- Updates docs/tests.

## Notes
If Jarvis still records too long, increase the base energy threshold with `stt energy 0.03` or `stt energy 0.04` and try `listen once` again.

If Jarvis misses quiet speech, lower it with `stt energy 0.012` or use `listen safer`.
