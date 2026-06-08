# Testing Guide — Jarvis Ultimate 0.0.5b LLM Structure Diagnostics

## 1. Install the patch

From the Jarvis Ultimate project root:

```powershell
python apply_0_0_5b_llm_structure_diagnostics_patch.py
```

## 2. Run the automated tests

```powershell
python -m unittest discover -s tests -v
```

Success should end with:

```text
Ran 42 tests
OK
```

## 3. Boot check

```powershell
python scripts/run_jarvis.py
```

Success should show:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 4. Manual CLI diagnostics

Start the CLI:

```powershell
python scripts/run_cli.py
```

Run:

```text
prompt stats
```

Success should show your provider, model, streaming setting, max tokens, prompt mode, and system prompt size.

## 5. Normal Jarvis timing test

In the CLI, send a normal message such as:

```text
hey jarvis
```

Then run:

```text
timing last
```

Look for:

```text
LM Studio prompt payload: ... bytes, ... prompt chars ...
Pre-LM Studio request time: ... ms
LM Studio time to first streamed chunk: ... ms
```

## 6. Direct LLM benchmark

Run:

```text
benchmark llm
```

This sends a direct benchmark request through the LM Studio provider while bypassing the Jarvis router and Conversation Agent.

Then test prompt variants:

```text
benchmark llm normal
benchmark llm minimal
benchmark llm off
```

Compare the `LM Studio time to first streamed chunk` from these tests against a normal Jarvis message.

## How to interpret the results

### If normal Jarvis is slower than `benchmark llm`

The delay is probably caused by Jarvis conversation structure, prompt size, message history, or future context injection.

Try setting this in `.env`:

```env
JARVIS_CONVERSATION_PROMPT_MODE=minimal
```

Then restart the CLI and compare again.

### If `benchmark llm` is about the same speed as normal Jarvis

The delay is probably not the Jarvis router/agent structure. It is likely LM Studio/model eval/settings, context size, GPU offload, prompt processing inside the server, or model-specific first-token latency.

### If `benchmark llm off` is much faster

The system prompt is contributing to the delay. Keep `minimal` for real-time chat, then use the full prompt only when Jarvis needs more careful behavior.

## Cleanup after success

After tests and manual checks pass, remove the installer files:

```powershell
Remove-Item apply_0_0_5b_llm_structure_diagnostics_patch.py
Remove-Item -Recurse patch_files
```

## Commit only after passing tests/manual checks

```powershell
git add .
git commit -m "0.0.5b Add LLM structure diagnostics"
git push
```
