# Jarvis Ultimate 0.0.5d — LM Studio Loopback Speed Cleanup

## Why this patch exists

During 0.0.5c testing, normal LM Studio API calls through `localhost` were taking about 2.3–2.6 seconds before the stream opened. Changing the OpenAI-compatible base URL to `127.0.0.1` dropped normal Jarvis response timing to roughly half a second to first streamed chunk on Tanner's machine.

This patch cleans that discovery into the project defaults and fixes native API diagnostics not reading the `JARVIS_LM_STUDIO_NATIVE_BASE_URL` value from the project-root `.env` file.

## Changes

- Default LM Studio OpenAI-compatible URL changed from `http://localhost:1234/v1` to `http://127.0.0.1:1234/v1`.
- Default LM Studio native diagnostic URL changed from `http://localhost:1234` to `http://127.0.0.1:1234`.
- `.env.example` now recommends `127.0.0.1` for both LM Studio URLs.
- `config/providers.yaml` now uses `127.0.0.1` for both LM Studio URLs.
- Added support for these native base URL aliases:
  - `JARVIS_LM_STUDIO_NATIVE_BASE_URL`
  - `JARVIS_LLM_STUDIO_NATIVE_BASE_URL`
  - existing `JARVIS_LLM_NATIVE_BASE_URL`
  - existing `JARVIS_LM_NATIVE_BASE_URL`
- `prompt stats` now warns if either LM Studio URL still uses `localhost`.
- Added loopback cleanup tests.
- Updated fast-path tests to expect the new direct loopback default.

## Expected impact

Normal Jarvis chat should continue using the fast OpenAI-compatible endpoint and should avoid the Windows `localhost` delay found during diagnostics.

The native endpoint remains a diagnostic option, not the main default path. It should now read the native URL value correctly from `.env`.

## Notes

If LM Studio is running on a different machine or non-default host, you can still override the URLs in `.env`.
