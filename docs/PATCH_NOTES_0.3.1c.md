# Jarvis Ultimate 0.3.1c — Entity Forget Routing Guard Hotfix

## Why this patch exists

Manual testing showed that Jarvis could still list Scout after the user said `Forget Scout.`

The remaining issue was routing, not the entity store itself. A plain command like `Forget Scout.` could fall through to normal conversation because the older deterministic memory phrase list matched `forget that` and `forget memory`, but not every natural `forget <name>` command. When that happened, the LLM could politely say it removed the information without actually sending the command to the Memory Agent.

## What changed

- `Forget Scout.`, `stop remembering Scout`, `delete memory Scout`, and similar commands now route directly to the Memory Agent.
- The Memory Agent now gets the chance to actually remove long-term, short-term, and entity memories instead of the conversation fallback only answering verbally.
- Added a regression test that saves Scout and Nugget, runs `Forget Scout.`, then verifies `List remembered pets.` only returns Nugget.
- App shell version is now `0.3.1c`.
- App shell capabilities now include `entity_memory_forget_routing_guard`.

## What did not change

- No changes to TTS, STT, wake-word behavior, app opening, UI layout, or local LLM settings.
- No changes to the entity schema beyond preserving the 0.3.1b cleanup behavior.
- No memory data is deleted automatically during patch install; Jarvis will delete Scout when you run the forget command again after applying this patch.

## Validation

Validated with:

```powershell
PYTHONPATH=src python -m unittest discover -s tests -v
```

Result:

```text
Ran 360 tests in 5.055s

OK
```
