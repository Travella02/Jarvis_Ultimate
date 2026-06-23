# Jarvis Ultimate 0.3.4a — Entity Phonetic Alias + Relationship Label Hotfix

## Purpose

This hotfix improves the 0.3.4 Relationship Memory Graph after live testing showed two related problems:

1. Jarvis could store `Kenleigh is my fiance`, but `Who is my fiancé?` could miss the relationship because accented and unaccented forms were not normalized the same way.
2. STT often hears `Kenleigh` as `Ken Lee`, so entity lookup and correction need conservative phonetic aliases.

## Changes

- Normalizes relationship labels across `fiance`, `fiancee`, `fiancé`, and `fiancée` to the canonical display label `fiancée`.
- Adds conservative phonetic aliases for person names, including patterns like `Kenleigh`, `Ken Lee`, `Ken Leigh`, and `Kenley`.
- Person entity records now automatically include those phonetic aliases for matching and search.
- Existing loaded person records get alias/relationship normalization backfilled when entity memory loads.
- Entity merge now treats the target side as canonical even when the target phrase resolves to the same record through an alias.
- This means `Ken Lee and Kenleigh are the same person` can rename the canonical record to `Kenleigh` instead of leaving `Ken Lee` as the visible name.
- Adds regression tests for the spelling/relationship/alias cases.
- Keeps the app-shell version at `0.3.4` so existing version-pinned tests remain stable; this patch is still delivered as the `0.3.4a` hotfix package.

## Expected behavior

After applying this patch:

- `Remember that Kenleigh is my fiance.` should save the relationship correctly.
- `Who is my fiancé?` should answer naturally with `Kenleigh is your fiancée, sir.`
- `Who is Ken Lee?` should still resolve to Kenleigh once Kenleigh is saved or merged.
- `Ken Lee and Kenleigh are the same person.` should preserve `Ken Lee` as an alias but make `Kenleigh` the canonical display name.

## Validation

Validated with:

```powershell
PYTHONPATH=src python -m unittest discover -s tests -v
```

Result:

```text
Ran 386 tests in 5.319s

OK
```
