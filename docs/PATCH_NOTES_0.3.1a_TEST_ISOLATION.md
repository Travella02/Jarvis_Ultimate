# Jarvis Ultimate 0.3.1a — Test Isolation Hotfix

This is a tiny hotfix for the one failing test Tanner saw after applying the 0.3.1a humanized entity-memory patch.

## What happened

The test `test_router_passes_entity_memory_to_memory_agent` created an `EntityMemoryStore()` without a temporary path.

That means it used the normal runtime file:

```text
data/memory/entities.json
```

After Jarvis had already remembered real entities during manual testing, the test expected exactly `1` entity record but found more records already saved. In Tanner's run, it found `4`.

## Fix

- The test now creates the entity-memory store in a temporary test directory.
- Real saved memories are no longer counted by this test.
- Runtime behavior is unchanged.
- Entity memory still persists normally when Jarvis is actually running.

## Files changed

- `tests/unit/test_memory_entities_031.py`
- `JARVIS_ULTIMATE_HANDOFF_INSTRUCTIONS.md`

## Version note

This does not change the app-shell/runtime version from `0.3.1a` because it is a test-suite isolation fix only.
