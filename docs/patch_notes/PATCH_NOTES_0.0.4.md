# Jarvis Ultimate 0.0.4 — LM Studio Latency Diagnostics + Fast Path

## Purpose

This patch targets the delay Tanner noticed before LM Studio receives a message from Jarvis. The model response itself may still take time, but 0.0.4 makes the pre-LLM path visible and removes one avoidable pre-chat lookup.

## What changed

### LM Studio fast path

- Jarvis no longer calls `GET /v1/models` before the first normal chat when the configured model is `auto`.
- `model: auto` now uses a local fast-path placeholder model name of `local-model` by default.
- If a future LM Studio setup needs the exact loaded model id, set this in `config/providers.yaml`:

```yaml
resolve_auto_model: true
```

or replace `model: auto` with the exact model id shown in LM Studio.

### Latency timing diagnostics

- Added a lightweight turn timer in `src/jarvis/core/timing.py`.
- Runtime now records timing marks for routing, intent classification, agent selection, conversation agent handling, LM Studio preparation, and LM Studio request/response timing.
- Every command result now includes timing data in `result.data["timing"]`.
- CLI now supports:

```text
timing last
```

### Clear pre-request vs request timing

The timing output now shows whether the delay happened:

- before `lm_studio.request_start`, meaning Jarvis/router/agent/provider prep overhead, or
- after `lm_studio.request_start`, meaning LM Studio/network/model server time.

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
- `tests/integration/test_runtime_timing_flow.py`
- `tests/unit/test_lm_studio_fast_path.py`
- `tests/unit/test_timing.py`
- `docs/TESTING_GUIDE_0.0.4.md`
- `docs/patch_notes/PATCH_NOTES_0.0.4.md`

## Expected test result

```text
Ran 26 tests
OK
```

## Commit message after testing passes

```bash
git add .
git commit -m "0.0.4 Add LM Studio latency diagnostics and fast path"
git push
```
