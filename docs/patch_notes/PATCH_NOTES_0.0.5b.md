# Jarvis Ultimate 0.0.5b — LLM Structure Diagnostics

## Goal

0.0.5b helps diagnose why the same LM Studio model can feel slower in the new Jarvis rebuild than it did in the older Jarvis project.

0.0.4 proved Jarvis gets to the LM Studio request in about 1–2 ms. 0.0.5 added streaming. 0.0.5a made the configured model name show correctly. This patch adds deeper structure diagnostics so we can compare the normal Jarvis route against a direct LLM call that bypasses the router and Conversation Agent.

## Added

- `prompt stats` CLI command.
- `benchmark llm` CLI command.
- `benchmark llm normal`, `benchmark llm minimal`, and `benchmark llm off` prompt-mode variants.
- Prompt/payload diagnostics in `timing last`.
- Configurable conversation system prompt mode:
  - `normal` = full Jarvis system prompt.
  - `minimal` or `fast` = short Jarvis system prompt.
  - `off` or `none` = no system prompt for testing.
- Configurable direct benchmark settings:
  - `JARVIS_LLM_BENCHMARK_MAX_TOKENS`
  - `JARVIS_LLM_BENCHMARK_PROMPT`
- New timing fields around the LM Studio payload:
  - `payload_bytes`
  - `prompt_chars`
  - `system_chars`
  - `user_chars`
  - `temperature`
  - `max_tokens`

## Why this matters

If `benchmark llm` is much faster than a normal Jarvis message, the slowdown is likely in the normal conversation structure, prompt, or future context. If `benchmark llm` has the same first-token delay as a normal Jarvis message, the slowdown is likely happening inside LM Studio/model eval/settings rather than Jarvis structure.

## Files changed

- `.env.example`
- `config/providers.yaml`
- `src/jarvis/agents/conversation_agent/agent.py`
- `src/jarvis/agents/conversation_agent/prompts.py`
- `src/jarvis/brain/router.py`
- `src/jarvis/clients/cli/cli_client.py`
- `src/jarvis/core/config.py`
- `src/jarvis/core/lifecycle.py`
- `src/jarvis/core/timing.py`
- `src/jarvis/providers/llm/lm_studio_provider.py`
- `tests/integration/test_llm_structure_diagnostics.py`
- `tests/unit/test_config_prompt_diagnostics.py`
- `tests/unit/test_conversation_prompt_modes.py`
- `tests/unit/test_lm_studio_payload_diagnostics.py`

## Expected tests

```powershell
python -m unittest discover -s tests -v
```

Expected result in the clean patch verification:

```text
Ran 42 tests
OK
```
