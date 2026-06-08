# Testing Guide — Jarvis Ultimate 0.0.5c

This patch is for diagnosing why LM Studio's direct chat UI feels faster than Jarvis's API path when Thinking is off.

## 1. Install the patch

From the Jarvis Ultimate root, run:

```powershell
python apply_0_0_5c_lm_studio_native_reasoning_diagnostics_patch.py
```

## 2. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Success should look like:

```text
Ran 48 tests
OK
```

Do not commit if tests fail.

## 3. Boot check

```powershell
python scripts/run_jarvis.py
```

Success should look like:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 4. Start the CLI

```powershell
python scripts/run_cli.py
```

Run:

```text
prompt stats
```

Success should show fields like:

```text
API mode: openai
native base URL: http://localhost:1234
reasoning/thinking: auto
context length override: default
```

## 5. Compare API request modes

Make sure LM Studio is open, a model is loaded, the Local Server is running, and Thinking is off in the LM Studio UI for the same model you are testing.

In Jarvis CLI, run each command twice. The first run can be slower because of warmup.

```text
benchmark lm openai
benchmark lm native
benchmark lm native off
```

Optional extra checks:

```text
benchmark lm native low
benchmark lm native auto
benchmark llm minimal
benchmark llm off
```

## 6. What to compare

After each benchmark, compare these lines:

```text
LM Studio time to first streamed chunk
LM Studio request/response time
LM Studio native stats
```

The key number is:

```text
LM Studio time to first streamed chunk
```

## 7. How to interpret the results

### If `benchmark lm native off` is much faster

That means the delay is probably caused by the OpenAI-compatible API path or by reasoning/thinking not being disabled through the current API request.

Next, set this in `.env`:

```env
JARVIS_LLM_API_MODE=native
JARVIS_LLM_NATIVE_BASE_URL=http://localhost:1234
JARVIS_LLM_REASONING=off
```

Restart the CLI and test a normal Jarvis message:

```text
hey jarvis

timing last
```

Success should show:

```text
api_mode=native
path=/api/v1/chat
reasoning=off
```

### If native mode errors

Possible causes:

- LM Studio version is too old for `/api/v1/chat`.
- The model does not support the requested reasoning setting.
- The server is running but native v1 endpoints are not available.

Try:

```text
benchmark lm native auto
```

If `native auto` works but `native off` fails, the model or LM Studio build may reject request-level reasoning controls for that model.

### If OpenAI and native are both slow

The issue is probably in LM Studio server settings or model runtime settings, not Jarvis structure. Compare these LM Studio settings against the older Jarvis setup:

- GPU offload
- context length
- Flash Attention
- KV cache
- quantization
- model load/runtime backend
- whether the model is warmed up

## 8. Cleanup after successful install

After tests and manual checks pass, remove the temporary installer files:

```powershell
Remove-Item apply_0_0_5c_lm_studio_native_reasoning_diagnostics_patch.py
Remove-Item -Recurse patch_files
```

## 9. Commit only after manual checks pass

Use this only after tests and the LM Studio benchmark comparison pass:

```powershell
git add .
git commit -m "0.0.5c Add LM Studio native API reasoning diagnostics"
git push
```
