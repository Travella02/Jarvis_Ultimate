# Jarvis Ultimate 0.3.4b — Relationship Display Cleanup Hotfix

## What changed

This hotfix fixes a display bug where merged relationship spellings could leak Python-style list formatting into Jarvis responses.

Example bad response:

```text
Kenleigh is your ['fiance fiancee', 'fiancée'], sir.
```

Expected response:

```text
Kenleigh is your fiancée, sir.
```

## Fixes

- Normalizes relationship display labels before Jarvis speaks them.
- Cleans merged `fiance` / `fiancee` / `fiancé` / `fiancée` variants into one canonical `fiancée` label.
- Handles legacy/list-style relationship attributes created by earlier 0.3.4a testing.
- Sanitizes relationship values before sending entity facts to the LLM humanizer.
- Adds a `relationship_display_cleanup` capability flag.

## Notes

This does not change the successful phonetic alias behavior. `Ken Lee`, `Kenley`, and similar conservative aliases can still resolve to `Kenleigh` when saved/merged correctly.
