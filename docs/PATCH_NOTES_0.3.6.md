# Jarvis Ultimate 0.3.6 — Sensitive Chat Redaction + Memory Log Hygiene

## Why this update exists

0.3.5a correctly routed passwords, bank/account numbers, API keys, and other sensitive save requests away from normal memory. Live testing showed one remaining security problem: the original user command could still be written into local chat archive/log files.

0.3.6 fixes that by redacting sensitive values before they are saved into normal local runtime files.

## Added

- Stronger sensitive-value redaction helpers in `jarvis.memory.secure_vault`.
- Recursive JSON-like payload redaction for logs, metadata, and app-shell status data.
- New `jarvis.memory.hygiene` module with `redact_sensitive_runtime_files(...)` for local upgrade cleanup.
- One-time installer cleanup for existing local runtime files.
- App-shell capabilities:
  - `sensitive_chat_archive_redaction`
  - `sensitive_ui_history_redaction`
  - `memory_log_hygiene_redaction`

## Changed

- Chat archive records redact sensitive user/assistant text before writing JSONL.
- Chat archive reads sanitize older records in memory before search/summarization.
- Memory candidates redact text, source user text, source assistant text, and metadata before saving.
- Short-term fact metadata is redacted defensively.
- UI chat messages redact sensitive values before staying in app-shell workspace state.
- Jarvis event/result logs redact sensitive values before writing JSONL.
- Voice session status redacts sensitive command/transcript/status fields before exposing them in API snapshots.
- App shell version is now `0.3.6`.

## Installer behavior

After copying files, the installer runs a one-time local hygiene pass over:

- `data/memory/chat_archive/**/*.jsonl`
- `data/memory/*.json`
- `data/conversations/**/*.json`
- `data/conversations/**/*.jsonl`
- `logs/**/*.jsonl`
- `logs/**/*.json`

This is meant to clean values that may already exist from earlier testing.

## What this does not do yet

- It does not create the full encrypted password manager.
- It does not store raw secrets in a vault yet.
- It does not guarantee that secrets never appear on screen while the user is actively typing them into an input field.
- It does not replace a dedicated Secure Vault / Password Manager Agent.

## Validation

Validated with:

```powershell
PYTHONPATH=src python -m unittest discover -s tests -v
```

Result:

```text
Ran 413 tests in 6.873s
OK
```
