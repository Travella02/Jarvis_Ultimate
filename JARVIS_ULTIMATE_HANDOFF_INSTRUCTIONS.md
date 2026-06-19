# Jarvis Ultimate Handoff Instructions

This file exists so a future ChatGPT project chat can quickly understand the current state of Jarvis Ultimate and continue without losing momentum.

## Current project status

Current committed milestone before this patch: **0.3.1 — Scalable Entity Memory Foundation**

Current patch milestone: **0.3.1a — Humanized Entity Memory Responses Hotfix**

Versioning rule: after `0.2.9`, use `0.3.0`, not `0.2.10`. Current version is `0.3.1a`. Hotfixes may use suffixes like `0.3.1a`.

## User patch/package preferences

For every Jarvis patch/update/fix package:

- Do not paste large code blocks in chat.
- Provide downloadable patch/replacement files.
- Include an installer script named like `apply_<version>_<summary>_patch.py`.
- Include a `patch_files/` folder.
- Include patch notes inside the patch package.
- Include a user-facing testing guide inside the patch package.
- Include direct “how to apply the patch” steps in the chat response.
- Run or validate the test suite before delivery whenever possible:
  ```powershell
  python -m unittest discover -s tests -v
  ```
- Do not include `START_HERE` files in patch packages.
- Do not include README files outside `patch_files/` in patch packages.
- Keep this handoff file updated with every patch.

## Current architecture summary

Jarvis Ultimate is a local-first AI assistant with:

- Python backend/runtime,
- Electron desktop app shell,
- local bridge API,
- LM Studio-compatible local LLM integration,
- Faster Whisper STT,
- Kokoro TTS,
- sleep/wake voice loop,
- animated orb UI,
- modular agents,
- App Agent,
- Memory Agent,
- early File Agent foundation,
- always-on memory foundation,
- structured Entity Memory foundation.

## App Agent current state

The App Agent is mostly complete for now.

Current abilities:

- open apps,
- close apps,
- focus/switch apps,
- app discovery/cache,
- taskkill fallback for app closing,
- launch verification,
- learned aliases,
- multiple aliases per app,
- default roles like browser/music/editor,
- list/forget/change aliases.

Possible future App Agent improvements:

- window resize/move/minimize/maximize,
- app picker when multiple close matches exist,
- richer action cards,
- better cross-platform support beyond Windows.

## Memory pipeline current state

Current memory abilities:

- explicit long-term memory save/search/forget,
- short-term memory with expiration,
- daily chat archive files,
- crash-safe JSON writes,
- LLM-based chat archive summarization,
- memory status command,
- incremental always-on memory persistence,
- memory candidate queue,
- automatic memory candidate capture,
- automatic short-term memory capture for recent context,
- candidate review commands,
- approve/promote candidate to long-term or short-term memory,
- reject candidate memories,
- structured entity memory store,
- scalable entity type registry,
- default entity types for user/person/pet/project/app/place/device/vehicle/organization,
- entity memory context injection,
- entity updates from explicit memories and approved candidates,
- humanized entity-memory replies with LLM rewriting when available and natural deterministic fallback responses.

Memory auto-capture design:

- Explicit “remember that…” commands still save directly through the Memory Agent.
- Non-memory turns can be analyzed after the response is ready.
- Obvious durable preferences/project rules become long-term candidates, not automatic permanent memories yet.
- Recent work/testing/daily context can be saved automatically as short-term memory.
- LLM-based memory classification is supported behind `JARVIS_MEMORY_AUTO_CAPTURE_LLM_REVIEW=false` by default, so the deterministic guardrails are used first.
- Candidate review is local-first and crash-safe.

Known memory design goals:

- Jarvis will eventually run for weeks or months at a time.
- Do not rely on restarts for memory processing or cleanup.
- Memory should persist incrementally while running.
- Future memory should include safer auto-promotion rules, richer entity extraction, user-controlled sensitive entity handling, workspaces/tenants for SaaS, routines/tasks/subscriptions, and eventually face identity memory.

## Next recommended update

Recommended next milestone: **0.3.2 Entity Memory Edit/Merge Controls + Memory Preferences** or **0.3.2 Memory Auto-Promotion Controls**.

Recommended goals:

- improve entity extraction for more natural phrasings,
- add commands like “remember things like this automatically” and “do not remember things like this,”
- add user-controlled auto-promotion preferences,
- add entity edit/merge/delete commands,
- add SaaS-ready scopes such as personal/workspace/team,
- keep sensitive/private memory behavior user-controlled.

## Public GitHub README update

A public-facing `README.md` was created to present Jarvis Ultimate as a portfolio/job-search project. It explains:

- project purpose,
- current capabilities,
- architecture,
- setup,
- testing,
- privacy/local data handling,
- version history,
- roadmap,
- recruiter/reviewer notes.

## 0.3.0c Local API Disconnect Guard Hotfix

This hotfix keeps the 0.3.0 memory auto-capture work intact and only improves local API bridge stability for long always-on sessions.

Changes:
- The local Python app-shell API now suppresses expected client disconnect socket errors such as `ConnectionAbortedError`, `BrokenPipeError`, and `ConnectionResetError` when Electron cancels a polling request.
- Real unexpected API errors still raise normally.
- This helps prevent scary terminal tracebacks during normal app-shell refresh/poll behavior.
- This does not change microphone/STT routing, memory behavior, or voice loop logic.

Current status:
- App Agent is stable enough for now.
- Memory foundation includes explicit long-term memory, short-term memory, chat archives, candidate review, duplicate filtering, and humanized memory responses.
- Superseded by 0.3.1 entity memory foundation; next recommended update is `0.3.2 Entity Memory Polish` or memory auto-promotion controls.

## 0.3.1 Scalable Entity Memory Foundation

This update adds structured entity memory beside long-term memory, short-term memory, chat archives, and candidate review.

Changes:
- Added `src/jarvis/memory/entities.py` with `EntityMemoryStore`, `EntityRecord`, `EntityTypeDefinition`, and conservative entity inference.
- Added default entity types: `user`, `person`, `pet`, `project`, `app`, `place`, `device`, `vehicle`, and `organization`.
- Added a registry-driven entity type model so future SaaS entity types can be added without schema changes.
- Added config flags for entity memory path, enablement, max records, and injection limit.
- Runtime now initializes `entity_memory` and passes it through the router context.
- Conversation Agent can inject relevant structured entity memory into the system prompt when relevant.
- Memory Agent can list/search entity memory and updates entity records from explicit saves and approved memory candidates.
- App shell snapshot includes entity-memory status.
- App shell version is now `0.3.1`.
- Added 0.3.1 tests and updated version assertions.

Current status:
- Full test suite passed in the patch workspace with `PYTHONPATH=src python -m unittest discover -s tests -v`.
- Result: `Ran 349 tests in 3.366s — OK`.

Important SaaS memory direction:
- Keep entity memory local-first and user-controlled by default.
- Use entity `scope`, `sensitivity`, and `metadata` fields later for workspace/team/tenant behavior.
- Do not store secrets such as passwords, API keys, card numbers, or SSNs as entity memories.


## 0.3.1a Humanized Entity Memory Responses Hotfix

This hotfix keeps the 0.3.1 scalable entity-memory foundation intact and improves the user-facing response layer.

Changes:
- Memory Agent entity search/list responses now use a natural Jarvis-style response path instead of exposing database-style text like `Structured entity memories`.
- When an LLM provider is available, entity answers are rewritten through the local LLM with strict instructions to use second-person wording such as `your fiancée`, `your dog`, and `your project`.
- If the LLM is unavailable, deterministic fallback responses are still natural, for example `Kenleigh is your fiancée, sir.`
- Entity summaries are converted away from `the user's ...` phrasing before being shown or injected into prompt context.
- Relationship extraction now supports multi-word names such as `Ken Lee is my fiance` and normalizes `fiance`/`fiancee` to `fiancée`.
- Entity type normalization now understands plurals like `pets`, `people`, `projects`, `apps`, `vehicles`, and `organizations`, fixing list commands such as `list remembered pets`.
- App shell version is now `0.3.1a` and capabilities include `entity_memory_humanized_responses`.

Current status:
- Full test suite passed in the patch workspace with `PYTHONPATH=src python -m unittest discover -s tests -v`.
- Result: `Ran 353 tests in 3.190s — OK`.

Next recommended update:
- Add entity edit/merge commands so Jarvis can correct STT mistakes like `Ken Lee` vs `Kenleigh` cleanly.
- Add memory preference controls for what Jarvis should auto-remember, ask about, or avoid remembering.

## 0.3.1a Test Isolation Hotfix

This hotfix only fixes a unit-test isolation issue discovered after real entity memories existed in `data/memory/entities.json`.

Changes:
- Updated `tests/unit/test_memory_entities_031.py` so `test_router_passes_entity_memory_to_memory_agent` uses a temporary entity-memory JSON file instead of the default runtime entity-memory path.
- This prevents the test from counting real saved entity memories such as people or pets that Jarvis has already learned during manual testing.
- No runtime memory behavior changed.
- No app-shell version change; the active runtime remains `0.3.1a`.

Current status:
- This keeps the 0.3.1/0.3.1a entity-memory behavior intact.
- The next recommended update remains entity edit/merge commands and memory preference controls.

## 0.3.1b Entity Forget Cleanup + Stale Response Guard Hotfix

This hotfix keeps the 0.3.1 scalable entity-memory foundation and 0.3.1a humanized responses intact, but fixes a real manual-testing issue where Jarvis said an entity was forgotten and then a later entity list could still mention it.

Changes:
- Entity memory `forget()` now removes all matching entity records directly by name, alias, source text, summary, and token match instead of depending only on ranked search results.
- Entity duplicate cleanup now merges loaded duplicate records that share names or aliases, which helps clean up early test data and STT/name variants.
- The LLM entity-response humanizer now has a stale-name guard. If the LLM tries to mention a proper-name entity that was not in the selected memory records, Jarvis falls back to the deterministic safe answer.
- Added tests for `Forget Scout` followed by `List remembered pets`, including a stale LLM response that tries to reintroduce Scout after only Nugget remains.
- App shell version is now `0.3.1b` and capabilities include `entity_memory_forget_cleanup_guard`.

Current status:
- Full test suite passed in the patch workspace with `PYTHONPATH=src python -m unittest discover -s tests -v`.
- Result: `Ran 357 tests in 4.999s — OK`.

Next recommended update:
- Add explicit entity edit/merge commands such as `Ken Lee and Kenleigh are the same person`, `rename Scout to ...`, and `forget only the pet named Scout`.
- Add memory preference controls for what Jarvis should auto-remember, ask about, or avoid remembering.

## 0.3.1c Entity Forget Routing Guard Hotfix

This hotfix keeps the 0.3.1 scalable entity-memory foundation, 0.3.1a humanized responses, and 0.3.1b entity cleanup intact, but fixes the remaining manual-testing issue where a plain command such as `Forget Scout.` could be routed to general conversation instead of the Memory Agent.

Root cause:
- `Forget Scout.` did not match the older deterministic memory phrase list because it only matched phrases like `forget that` or `forget memory`.
- The ability fallback could also score slightly under its threshold when punctuation was included.
- When the command went to general chat, the LLM could politely say it removed the information without actually deleting the entity memory.

Changes:
- The intent classifier now treats plain entity/memory deletion commands like `Forget Scout.`, `stop remembering Scout`, `delete memory Scout`, and `do not remember Scout` as `memory_write` commands.
- This forces real forget/delete commands through the Memory Agent instead of conversation fallback.
- Added a regression test proving `Forget Scout.` routes to `memory_agent`, removes Scout, and then `List remembered pets.` only returns Nugget.
- App shell version is now `0.3.1c` and capabilities include `entity_memory_forget_routing_guard`.

Current status:
- Full test suite passed in the patch workspace with `PYTHONPATH=src python -m unittest discover -s tests -v`.
- Result: `Ran 360 tests in 5.055s — OK`.

Next recommended update:
- Add explicit entity edit/merge commands such as `Ken Lee and Kenleigh are the same person`, `rename Scout to ...`, and `forget only the pet named Scout`.
- Add memory preference controls for what Jarvis should auto-remember, ask about, or avoid remembering.
