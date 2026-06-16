# Jarvis Ultimate 0.3.0 — Memory Auto-Capture + Candidate Review

## Summary

This update upgrades the memory system from explicit-only memory into the first automatic memory review pipeline. Jarvis can now notice possible memories after normal conversations, store them in a local candidate queue, automatically save useful short-term context, and let the user approve or reject possible long-term memories.

## Added

- Memory candidate queue at `data/memory/memory_candidates.json`.
- Crash-safe candidate writes using the existing always-on memory write pattern.
- Automatic memory candidate capture after completed turns.
- Automatic short-term memory capture for recent context.
- Candidate review commands:
  - `Jarvis, what memories are waiting for review?`
  - `Jarvis, what did you learn recently?`
  - `Jarvis, save that permanently.`
  - `Jarvis, promote that.`
  - `Jarvis, reject that.`
  - `Jarvis, forget that candidate.`
- Candidate approval can promote a pending candidate to long-term memory or short-term memory depending on its suggested tier.
- LLM-ready memory tier classification behind a safe config flag.
- New memory config values in `.env.example`.
- App shell version updated to `0.3.0`.
- App shell runtime snapshot now includes memory candidate status.
- Handoff file updated for the new current state.

## Important design choice

Automatic permanent memory is **not** fully enabled yet. Jarvis now captures likely long-term facts as review candidates. This keeps the system safer while we tune the memory classifier and review workflow.

## Notes

The default memory classifier is deterministic for speed and stability. Optional LLM classification is available with:

```env
JARVIS_MEMORY_AUTO_CAPTURE_LLM_REVIEW=true
```

Keep that off by default until the behavior is tested more.
