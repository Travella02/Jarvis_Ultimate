# Jarvis Ultimate 0.0.5a — LM Studio Config Cleanup

## Purpose

This small cleanup patch fixes the confusing model-name behavior Tanner noticed after 0.0.5. Editing the project-root `.env` file now actually affects Jarvis config, and Jarvis also accepts the shorter `JARVIS_LM_*` variable names that were already being used locally.

## What changed

### Project `.env` loading

- Jarvis now reads a simple `.env` file from the project root without adding any new dependency.
- Real OS environment variables still have highest priority.
- `.env` values come next.
- `config/providers.yaml` remains the safe committed fallback.

### LM Studio environment aliases

Jarvis now accepts both the canonical `JARVIS_LLM_*` names and the shorter `JARVIS_LM_*` aliases for local LM Studio settings.

Supported aliases include:

```text
JARVIS_LLM_PROVIDER / JARVIS_LM_PROVIDER
JARVIS_LLM_MODEL / JARVIS_LM_MODEL
JARVIS_LLM_TIMEOUT_SECONDS / JARVIS_LM_TIMEOUT_SECONDS
JARVIS_LLM_TEMPERATURE / JARVIS_LM_TEMPERATURE
JARVIS_LLM_MAX_TOKENS / JARVIS_LM_MAX_TOKENS
JARVIS_LLM_STREAMING / JARVIS_LM_STREAMING
JARVIS_LLM_RESOLVE_AUTO_MODEL / JARVIS_LM_RESOLVE_AUTO_MODEL
```

For the LM Studio URL, Jarvis accepts:

```text
JARVIS_LM_STUDIO_BASE_URL
JARVIS_LLM_STUDIO_BASE_URL
JARVIS_LLM_BASE_URL
```

### Cleaner model logging

If `.env` contains an exact model id such as:

```text
JARVIS_LM_MODEL=google/gemma-4-12b-qat
```

then `timing last` should show that configured model instead of falling back to `local-model`.

## Files changed

- `.env.example`
- `config/providers.yaml`
- `src/jarvis/core/config.py`
- `tests/unit/test_env_file_config.py`
- `docs/TESTING_GUIDE_0.0.5a.md`
- `docs/patch_notes/PATCH_NOTES_0.0.5a.md`

## Expected test result

```text
Ran 33 tests
OK
```

## Commit message after testing passes

```bash
git add .
git commit -m "0.0.5a Clean up LM Studio env config"
git push
```
