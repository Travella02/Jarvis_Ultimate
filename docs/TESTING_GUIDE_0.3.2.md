# Jarvis Ultimate 0.3.2 Testing Guide — Entity Merge + Alias Correction

Run these checks after applying the patch.

## 1. Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_2_entity_merge_alias_patch.py
```

## 2. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

If Python cannot import the `jarvis` package in a fresh PowerShell window, run:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

## 3. Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

Or double-click:

```powershell
Start_Jarvis_Ultimate_App.bat
```

## 4. Manual entity correction checks

Try this sequence:

```text
Remember that Ken Lee is my fiancée.
Who is Ken Lee?
Ken Lee and Kenleigh are the same person.
Who is Ken Lee?
Who is Kenleigh?
```

Expected result:

- Jarvis should answer naturally.
- Jarvis should not say `Structured entity memories`.
- After the merge, both `Ken Lee` and `Kenleigh` should resolve to the corrected canonical entity.

## 5. Manual rename check

Try:

```text
Remember that Lee is my fiancée.
Change Lee to Kenleigh.
Who is Lee?
Who is Kenleigh?
```

Expected result:

- Jarvis should rename the entity to `Kenleigh`.
- `Lee` should remain as an alias, not as a separate duplicate entity.

## 6. Manual alias add/remove check

Try:

```text
Add Ken Lee as an alias for Kenleigh.
Who is Ken Lee?
Forget the alias Ken Lee, but keep Kenleigh.
Who is Ken Lee?
Who is Kenleigh?
```

Expected result:

- After adding the alias, `Ken Lee` should resolve to `Kenleigh`.
- After forgetting the alias, Jarvis should keep `Kenleigh` saved.
- Removing the alias should not delete the entity.

## 7. Manual pet alias check

Try:

```text
Remember that my dog Nugget is a golden doodle.
Nugget and Nuggie are the same dog.
Who is Nuggie?
List remembered pets.
```

Expected result:

- `Nuggie` should resolve to `Nugget`.
- The pet list should not create duplicate pets.

## Common issues

If Jarvis says it cannot find enough saved entity memory to merge two names, make sure at least one of those names has already been saved as entity memory first.

If Jarvis routes an alias correction to the App Agent, re-run the tests and make sure `src/jarvis/brain/intent_classifier.py` was patched correctly.

If an old duplicate still appears, try merging it explicitly with the canonical name or forgetting the duplicate after confirming the alias was preserved.
