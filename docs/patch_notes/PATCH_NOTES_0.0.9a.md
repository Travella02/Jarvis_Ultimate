# Patch Notes — 0.0.9a STT Windows Path Hotfix

## Summary
Fixes a Windows-only unit test failure in the STT microphone foundation patch.

## Problem
On Windows, `Path("data/stt/sample.wav")` displays as `data\\stt\\sample.wav`, but the test expected `data/stt/sample.wav`.

## Fix
`format_record_result()` now normalizes displayed output paths to forward slashes for stable CLI output and cross-platform tests.

## Changed files
- `src/jarvis/providers/stt/audio_recorder.py`

## Expected result
`python -m unittest discover -s tests -v` should pass after applying this hotfix.
