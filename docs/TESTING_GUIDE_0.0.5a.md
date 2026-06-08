# Jarvis Ultimate 0.0.5a Testing Guide

## Goal

Confirm that Jarvis now reads LM Studio settings from your project-root `.env` file and that `timing last` shows your configured model name instead of always showing `local-model`.

## 1. Install the patch

From the extracted patch folder, copy these into your Jarvis Ultimate project root:

```text
apply_0_0_5a_lm_studio_config_cleanup_patch.py
patch_files/
```

Your project root is usually:

```text
C:\Users\tanne\Desktop\Jarvis_Ultimate
```

Then run:

```powershell
python apply_0_0_5a_lm_studio_config_cleanup_patch.py
```

## 2. Check your `.env`

Open your project-root `.env` file.

This now works:

```env
JARVIS_LM_MODEL=google/gemma-4-12b-qat
```

This also works:

```env
JARVIS_LLM_MODEL=google/gemma-4-12b-qat
```

Use the exact model id shown by LM Studio if you want clean model logs. `auto` still works if you prefer the LM Studio fast path placeholder.

## 3. Run the automated tests

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 33 tests
OK
```

## 4. Boot check

Run:

```powershell
python scripts/run_jarvis.py
```

Expected result:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 5. Manual CLI check

Make sure LM Studio is open, the local server is running, and your chosen model is loaded.

Run:

```powershell
python scripts/run_cli.py
```

Send a normal message, then run:

```text
timing last
```

Success looks like this somewhere in the timing output:

```text
lm_studio.model_resolved ... mode=configured, model=google/gemma-4-12b-qat
```

The exact model text should match your `.env` value.

## 6. What common results mean

If you still see:

```text
model=local-model
```

then Jarvis is still using `auto`, or your `.env` file is not in the project root you are running from.

If the model name is correct but time to first chunk is still around 2–3 seconds, that delay is still inside LM Studio/model generation, not Jarvis config.

## 7. Cleanup after everything passes

After the tests and manual check pass, remove the temporary installer files:

```powershell
Remove-Item apply_0_0_5a_lm_studio_config_cleanup_patch.py
Remove-Item -Recurse patch_files
```

## 8. Commit only after tests and manual checks pass

```powershell
git add .
git commit -m "0.0.5a Clean up LM Studio env config"
git push
```
