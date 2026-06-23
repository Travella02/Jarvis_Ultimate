# Jarvis Ultimate 0.3.7 — Memory Review Panel + Spoken Summary Control

## What changed

- Added a ranked Memory Review builder for detailed "show everything you remember about..." requests.
- Added a `memory_review` UI panel type and workspace card payload for ranked bullet lists.
- Memory reviews combine entity memory, relationship graph facts, long-term memory, and short-term facts.
- Jarvis now speaks only a short confirmation for visual review requests, such as: "Here is everything I know about Kenleigh, sir."
- Jarvis only reads the full ranked list out loud when the user asks to speak/read/tell everything.
- Memory review bullets are ranked by importance, relevance score, and memory tier.
- Sensitive redaction is preserved in panel payloads and spoken review formatting.
- App shell version updated to `0.3.7`.

## Why it matters

This makes Jarvis feel more like a real visual assistant instead of a chat-only bot. Long memory reviews belong in Jarvis's interface, not in a long spoken monologue, unless the user specifically asks him to read it.

## Example commands

- `Show everything you remember about Kenleigh.`
- `Show all you know about Nugget.`
- `Open memory review for Jarvis.`
- `Speak everything you remember about Kenleigh.`
- `Read my full memory review about Nugget.`

## Validation

Validated with:

```powershell
PYTHONPATH=src python -m unittest discover -s tests -v
```

Result:

```text
Ran 419 tests in 6.452s
OK
```
