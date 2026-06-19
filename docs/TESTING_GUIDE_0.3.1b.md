# Jarvis Ultimate 0.3.1b Testing Guide

## 1. Apply the patch

From your Jarvis project root, run:

```powershell
python apply_0_3_1b_entity_forget_cleanup_patch.py
```

## 2. Run the automated tests

```powershell
python -m unittest discover -s tests -v
```

If imports fail in a fresh PowerShell window, run:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

The patch workspace passed with:

```text
Ran 357 tests in 4.999s
OK
```

## 3. Manual memory test

Start Jarvis, then try this exact flow:

```text
Remember that my dog Scout is a golden doodle.
Remember that my dog Nugget is a golden doodle.
Who is Scout?
Forget Scout.
List remembered pets.
```

Expected behavior:

- Jarvis can answer that Scout is your dog before forgetting.
- After `Forget Scout`, Jarvis should confirm the memory was removed.
- `List remembered pets` should mention Nugget only.
- Scout should not appear in the pet list unless you save Scout again.

## 4. Optional follow-up checks

Try:

```text
Who is Scout?
```

Expected behavior:

- Jarvis should say he does not have anything saved about Scout, or otherwise avoid claiming Scout is still remembered.

Try:

```text
Entity memory status.
```

Expected behavior:

- The pet count should match the pets still saved after deletion.

## 5. Common issues

If Scout still appears after applying this patch, fully close and restart Jarvis so the runtime reloads the patched memory code.

If a test fails because of real saved memories in `data/memory`, check that the 0.3.1a test isolation hotfix was already applied. This patch assumes your project has the 0.3.1a hotfix chain applied.
