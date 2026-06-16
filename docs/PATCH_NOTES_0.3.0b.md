# Patch Notes — 0.3.0b Memory Duplicate Filtering Hotfix

This hotfix improves the 0.3.0 memory candidate review flow after real UI testing.

## Fixed

- Candidate review no longer lists the same memory twice when two raw captures mean the same thing.
- Long-term memory recall no longer repeats equivalent facts such as `I prefer...` and `you prefer...`.
- Promoting duplicate candidates saves one durable memory instead of multiple copies.
- Existing duplicate records are de-duplicated when memory stores load.
- Short-term memory formatting also de-duplicates equivalent user-facing facts.

## Notes

This keeps the visible app-shell version at the 0.3.0 milestone while fixing the uncommitted 0.3.0 memory work.
