# Testing Guide — 0.0.5d LM Studio Loopback Speed Cleanup

## Goal

Verify that Jarvis now defaults to direct loopback LM Studio URLs, reads the native LM Studio URL from `.env`, warns about `localhost`, and keeps normal streaming chat working.

## Before testing

Make sure LM Studio is open, a model is loaded, and the local server is running.

From the Jarvis Ultimate root, activate your venv first.

## 1. Install the patch

Copy these into the Jarvis Ultimate project root:

```powershell
apply_0_0_5d_lm_studio_loopback_speed_cleanup_patch.py
patch_files/
```

Run:

```powershell
python apply_0_0_5d_lm_studio_loopback_speed_cleanup_patch.py
```

## 2. Check your `.env`

Your `.env` should include:

```env
JARVIS_LM_STUDIO_BASE_URL=http://127.0.0.1:1234/v1
JARVIS_LM_STUDIO_NATIVE_BASE_URL=http://127.0.0.1:1234
```

Keep your model line as whatever you are currently testing, for example:

```env
JARVIS_LM_MODEL=google/gemma-4-12b-qat
```

## 3. Run automated tests

```powershell
python -m unittest discover -s tests -v
```

Expected success:

```text
Ran 54 tests
OK
```

## 4. Boot check

```powershell
python scripts/run_jarvis.py
```

Expected success:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 5. CLI diagnostics

```powershell
python scripts/run_cli.py
```

Run:

```text
prompt stats
```

Success should show:

```text
base URL: http://127.0.0.1:1234/v1
native base URL: http://127.0.0.1:1234
```

It should not show a `localhost` warning unless your `.env` still uses `localhost`.

## 6. Normal chat timing check

In the CLI, run:

```text
hey jarvis
```

Then run:

```text
timing last
```

Success should show a fast OpenAI-compatible path similar to:

```text
api_mode=openai
path=/chat/completions
Pre-LM Studio request time: a few ms
LM Studio time to first streamed chunk: much lower than the old 2400–2600 ms delay
```

On Tanner's machine, switching to `127.0.0.1` dropped the first streamed chunk to roughly 0.5 seconds in a normal Jarvis message.

## 7. Native diagnostics check

Run:

```text
benchmark lm native off
```

Then check the output for:

```text
native_base_url=http://127.0.0.1:1234
```

The native endpoint is still diagnostic only. It does not need to beat the OpenAI-compatible path for this patch to pass. The important check is that Jarvis reads the native URL correctly from `.env`.

## 8. Cleanup after success

After the tests and manual checks pass, remove the installer files:

```powershell
Remove-Item apply_0_0_5d_lm_studio_loopback_speed_cleanup_patch.py
Remove-Item -Recurse patch_files
```

Then commit:

```powershell
git add .
git commit -m "0.0.5d Clean up LM Studio loopback URLs"
git push
```

Only commit after automated tests and manual timing checks pass.
