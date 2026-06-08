# Jarvis Ultimate 0.0.5 — Streaming LM Studio Responses

## Purpose

0.0.4 proved that Jarvis now sends messages to LM Studio almost instantly. The remaining wait is mostly inside LM Studio/model generation time. This patch makes Jarvis feel faster by streaming LM Studio response chunks to the CLI as they arrive instead of waiting for the full response to finish.

## What changed

### LM Studio streaming path

- Added OpenAI-compatible streaming support for `POST /v1/chat/completions`.
- When a client provides a stream callback, Jarvis now sends `stream: true` in the LM Studio chat payload.
- Jarvis parses server-sent event lines such as:

```text
data: {"choices":[{"delta":{"content":"Hello"}}]}
data: [DONE]
```

- Jarvis still collects the full final response internally, so downstream agents, logs, memory, and future UI clients can still receive a complete `JarvisResult`.

### CLI streamed output

- `python scripts/run_cli.py` now prints streamed conversation chunks immediately.
- Normal commands such as `status`, `list agents`, and `screen check` still print normally.
- If streaming fails before any chunks are printed, Jarvis falls back to the normal error message path.

### Streaming timing diagnostics

`timing last` now includes extra streaming timing when available:

- `lm_studio.stream_opened`
- `lm_studio.first_chunk`
- `lm_studio.stream_done`
- `LM Studio time to first streamed chunk`
- `LM Studio remaining stream time`

This should show how quickly Jarvis starts receiving the first visible part of the model answer.

### Config flag

Added this to `config/providers.yaml`:

```yaml
streaming: true
```

You can temporarily disable streaming by setting:

```yaml
streaming: false
```

or by using the environment variable:

```powershell
$env:JARVIS_LLM_STREAMING="false"
```

## Files changed

- `config/providers.yaml`
- `src/jarvis/agents/conversation_agent/agent.py`
- `src/jarvis/brain/router.py`
- `src/jarvis/clients/cli/cli_client.py`
- `src/jarvis/core/config.py`
- `src/jarvis/core/lifecycle.py`
- `src/jarvis/core/timing.py`
- `src/jarvis/providers/llm/base.py`
- `src/jarvis/providers/llm/factory.py`
- `src/jarvis/providers/llm/lm_studio_provider.py`
- `src/jarvis/providers/llm/mock_provider.py`
- `tests/integration/test_runtime_streaming_flow.py`
- `tests/unit/test_config_streaming.py`
- `tests/unit/test_lm_studio_streaming.py`
- `docs/TESTING_GUIDE_0.0.5.md`
- `docs/patch_notes/PATCH_NOTES_0.0.5.md`

## Expected test result

```text
Ran 30 tests
OK
```

## Commit message after testing passes

```bash
git add .
git commit -m "0.0.5 Add streaming LM Studio responses"
git push
```
