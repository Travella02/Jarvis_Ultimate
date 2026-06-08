# Jarvis Ultimate 0.0.5c — LM Studio Native API + Reasoning Diagnostics

## Why this patch exists

Tanner confirmed that Qwen and Gemma respond almost instantly inside LM Studio's own chat UI when Thinking is off, but the same model feels slower through Jarvis's API path. The 0.0.5b diagnostics proved Jarvis's router, agent registry, and prompt size are not adding the two-second delay. This patch adds request-mode diagnostics so Jarvis can compare LM Studio's OpenAI-compatible API against LM Studio's native API and explicitly test reasoning/thinking controls.

## Added

- LM Studio provider support for two API modes:
  - `openai` = `/v1/chat/completions`
  - `native` = `/api/v1/chat`
- Native LM Studio streaming parser for named SSE events such as:
  - `prompt_processing.start`
  - `prompt_processing.end`
  - `reasoning.start`
  - `reasoning.end`
  - `message.delta`
  - `chat.end`
- Native payload support for:
  - `reasoning: off | low | medium | high | on`
  - `context_length`
  - `store: false`
  - `max_output_tokens`
  - `system_prompt`
- CLI benchmark commands for request-mode comparison:
  - `benchmark lm openai`
  - `benchmark lm native`
  - `benchmark lm native off`
  - `benchmark lm native low`
  - `benchmark lm native auto`
- `prompt stats` now reports:
  - API mode
  - native base URL
  - reasoning/thinking setting
  - context length override
- `timing last` now reports:
  - API mode
  - endpoint path
  - reasoning setting
  - context length when used
  - native LM Studio stats if returned, including TTFT and reasoning token count
- New `.env` and `providers.yaml` settings:
  - `JARVIS_LLM_API_MODE`
  - `JARVIS_LLM_NATIVE_BASE_URL`
  - `JARVIS_LLM_REASONING`
  - `JARVIS_LLM_CONTEXT_LENGTH`
  - `JARVIS_LLM_STORE_NATIVE_CHATS`

## Kept compatible

- Default mode remains `openai` so existing LM Studio behavior stays compatible.
- The native API mode can be tested from CLI without changing `.env` first.
- `benchmark llm off` still means “system prompt off” unless an API mode is included.
- `benchmark lm native off` means “native API with reasoning/thinking off.”

## Files changed

- `.env.example`
- `config/providers.yaml`
- `src/jarvis/clients/cli/cli_client.py`
- `src/jarvis/core/config.py`
- `src/jarvis/core/lifecycle.py`
- `src/jarvis/core/timing.py`
- `src/jarvis/providers/llm/factory.py`
- `src/jarvis/providers/llm/lm_studio_provider.py`
- `tests/integration/test_llm_structure_diagnostics.py`
- `tests/unit/test_lm_studio_native_api.py`
- `tests/unit/test_native_config.py`

## Test result from patch build

```text
Ran 48 tests
OK
```

Boot check:

```text
Jarvis 3 is online. Registered 9 agents.
```
