# Patch Notes — 0.3.0a Memory Candidate Response Humanization Hotfix

## Summary

This hotfix improves how Jarvis speaks about memory candidates and saved user memories. It keeps the 0.3.0 memory auto-capture foundation, but makes review/recall responses sound less like internal records and more like Jarvis naturally talking to the user.

## Changes

- Humanized memory candidate review responses.
- Removed visible confidence-score wording from normal candidate review speech.
- Improved first-person to second-person conversion when Jarvis recalls user memories.
- Strips command framing like `from now on` / `going forward` from saved candidate text.
- Long-term memory recall now handles standalone `I` phrases better.
- Short-term memory recall uses the same improved user-context wording.
- Added regression tests for candidate review and promoted candidate recall.
- Updated `JARVIS_ULTIMATE_HANDOFF_INSTRUCTIONS.md`.

## Notes

The app shell visible version remains `0.3.0` so older UI version tests stay compatible. This is a hotfix applied to the uncommitted 0.3.0 memory update.
