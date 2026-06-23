# Jarvis Ultimate Handoff Instructions

This file exists so a future ChatGPT project chat can quickly understand the current state of Jarvis Ultimate and continue without losing momentum.

## Current project status

Current committed milestone before this patch: **0.3.3a — Typed Input Voice Parity + Natural Memory Response Hotfix**

Current patch milestone: **0.3.4 — Relationship Memory Graph**

Versioning rule: after `0.2.9`, use `0.3.0`, not `0.2.10`. Current working version is `0.3.4`. Hotfixes may use suffixes like `0.3.2a`.

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
- After the unittest command in the final instructions, include the Jarvis start command too:
  ```powershell
  python scripts\start_jarvis_app.py
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
- structured Entity Memory foundation,
- relationship memory graph for people/pets/projects/devices and future SaaS workspaces.

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
- humanized entity-memory replies with LLM rewriting when available and natural deterministic fallback responses,
- entity merge/rename/alias correction commands for fixing STT/name mistakes.

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

Recommended next milestone: **0.3.3 Relationship Memory Graph** or **0.3.3 Memory Preferences / Auto-Remember Controls**.

Recommended goals:

- add richer relationship graph traversal between entities,
- add commands like “remember things like this automatically” and “do not remember things like this,”
- add user-controlled auto-promotion preferences,
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


## 0.3.2 Entity Merge + Alias Correction

This update builds on the 0.3.1 entity-memory foundation and the 0.3.1a-c hotfixes by adding explicit correction controls for names, aliases, STT mistakes, and duplicate entity records.

Changes:
- Added `EntityMemoryStore.resolve()` for exact-first entity/name/alias resolution.
- Added `EntityMemoryStore.merge()` so commands like `Ken Lee and Kenleigh are the same person` can collapse duplicate records while preserving aliases and details.
- Added `EntityMemoryStore.rename()` so commands like `Change Lee to Kenleigh` rename the canonical entity while keeping the old name as an alias.
- Added `EntityMemoryStore.add_alias()` and `remove_alias()` for commands like `Add Ken Lee as an alias for Kenleigh` and `Forget the alias Ken Lee, but keep Kenleigh`.
- Memory Agent now handles entity edit actions before normal search/list/save commands.
- Intent classifier routes entity merge, rename, alias-add, and alias-remove phrases to the Memory Agent instead of app control or general chat.
- App shell version is now `0.3.2` and capabilities include `entity_memory_merge_alias_correction`.

Manual examples:
- `Ken Lee and Kenleigh are the same person.`
- `Change Lee to Kenleigh.`
- `Add Ken Lee as an alias for Kenleigh.`
- `Forget the alias Ken Lee, but keep Kenleigh.`
- `Who is Ken Lee?` should now resolve to the canonical saved entity.

Current status:
- Full test suite passed in the patch workspace with `PYTHONPATH=src python -m unittest discover -s tests -v`.
- Result: `Ran 368 tests in 3.717s — OK`.

Next recommended update:
- `0.3.3 Relationship Memory Graph` so Jarvis can reason over links such as fiancée, pet owner, project contributor, device ownership, organization membership, and SaaS workspace/team scopes.
- Or `0.3.3 Memory Preferences / Auto-Remember Controls` so users can decide what Jarvis may remember automatically, what requires approval, and what should never be saved.


## 0.3.3 Typed Input Voice Parity

This update pauses the memory pipeline briefly to fix a core interaction issue: typed commands in the Jarvis interface should behave like intentional voice commands, not like a separate silent chat path.

Changes:
- `/api/command` now treats typed app-shell commands as intentional Jarvis turns and does not require a wake word.
- Typed app-shell commands now route through the normal runtime brain/agent pipeline and can use memory, tools, and agents exactly like voice commands.
- Typed responses now use the spoken response pipeline, so Jarvis reads answers aloud when TTS is available.
- Complete non-streamed tool/agent replies still get pre-speech caption staging so short responses appear under the orb before/while Jarvis says them.
- Running sleep/wake voice sessions are preserved after a typed turn; typed commands should no longer make Jarvis look idle or stop listening.
- The app-shell renderer now sends `speak: true` and `input_mode: typed` for normal typed commands.
- The desktop/Tk fallback typed command path also uses spoken playback and returns to the voice-running visual state when the desktop voice runtime is active.
- App shell version is now `0.3.3` and capabilities include `typed_input_voice_parity`.

Manual examples:
- Start Jarvis with `python scripts\start_jarvis_app.py`.
- Let sleep/wake mode start.
- Type `Who is Kenleigh?` without saying a wake word.
- Jarvis should answer aloud and still keep voice sleep/wake available afterward.
- Then say `Hey Jarvis, what do you remember about Kenleigh?` to verify voice still works.

Current status:
- Full test suite passed in the patch workspace with `PYTHONPATH=src python -m unittest discover -s tests -v`.
- Result: `Ran 371 tests in 3.564s — OK`.

Next recommended update:
- Return to the memory pipeline with `0.3.4 Relationship Memory Graph`, or add `0.3.4 Memory Preferences / Auto-Remember Controls` if user control over automatic memory should come first.


## 0.3.3a Typed Input Stabilization + Natural Memory Search Hotfix

This hotfix should be applied before committing 0.3.3. It keeps the 0.3.3 typed-input voice parity work intact and fixes two manual-testing issues found in the Jarvis app shell.

Root causes:
- `What do you remember about Kenleigh?` used the combined memory-search formatter, which still had database-style wording such as `structured entity memory` even though direct entity questions were already humanized.
- While a typed response was being spoken, the background sleep/wake voice thread could keep polling the mic and overwrite the orb state back to sleeping/listening, causing fast state flicker during typed replies.

Changes:
- Combined memory search now humanizes entity-only and mixed memory answers.
- Entity memory names are displayed more naturally for person/pet records when STT stores lower-case names.
- LLM humanization is now used for `what do you remember about...` memory-search responses when an LLM provider is available, with deterministic natural fallback when it is not.
- App-shell typed turns now hold the visible speaking/thinking state while background sleep/wake continues running.
- Background sleep/wake visual updates are suppressed during typed response playback, without stopping the microphone loop.
- App shell version is now `0.3.3a` and capabilities include `typed_input_visual_hold` and `humanized_memory_search_responses`.

Manual examples:
- Type `What do you remember about Kenleigh?` and Jarvis should answer naturally, such as `Kenleigh is your fiancée, sir.`
- Type a command while sleep/wake is running; Jarvis should speak the response without flickering rapidly between speaking and sleeping.
- After the typed turn, voice sleep/wake should still be available.

Current status:
- Full test suite passed in the patch workspace with `PYTHONPATH=src python -m unittest discover -s tests -v`.
- Result: `Ran 374 tests in 4.984s — OK`.

Next recommended update:
- Commit `0.3.3a` after manual testing succeeds.
- Then return to the memory pipeline with `0.3.4 Relationship Memory Graph` or `0.3.4 Memory Preferences / Auto-Remember Controls`.


## 0.3.3a App Agent Test-Isolation Hotfix

This small follow-up hotfix keeps the 0.3.3a typed-memory response changes intact and only fixes test isolation.

Changes:
- Updated `tests/unit/test_app_agent_launch_verification_026.py` so App Agent launch-verification tests do not inspect the real machine's currently running Discord process.
- Patched `_candidate_is_running` to `False` inside the two launch-verification tests that expect mocked launch behavior.
- Replaced the hardcoded real-user Discord path fixture with a neutral `JarvisTest` path.
- No runtime behavior changed.
- No app-shell version bump; the active runtime remains `0.3.3a`.

Current status:
- Full test suite passed in the patch workspace with `PYTHONPATH=src python -m unittest discover -s tests -v`.
- Result: `Ran 374 tests in 4.280s — OK`.
- After this test-isolation fix, Tanner should retest 0.3.3a typed input manually, then commit the 0.3.3/0.3.3a typed-input work.

Next recommended update after commit:
- Resume the memory roadmap with Relationship Memory Graph or Memory Preferences / Auto-Remember Controls.

## 0.3.4 Relationship Memory Graph

This milestone builds on 0.3.1–0.3.3a entity memory and adds a scalable relationship layer inside entity memory.

Changes:
- Entity records can now be queried as relationship-graph edges instead of only isolated facts.
- Relationship edges support source entity, relationship type, target entity/user, scope, confidence, and raw metadata.
- Existing person relationships such as “Kenleigh is my fiancée” become graph edges to the user.
- Pet memories such as “my dog Nugget is a golden doodle” become relationship edges to the user.
- Project memories such as Jarvis project references can be represented as user/project relationships.
- Cross-entity project relationships such as “Kenleigh works on Jarvis” can be queried.
- Memory Agent now answers natural relationship questions without exposing structured/database wording.
- Intent classifier routes relationship questions to memory instead of general chat.
- App shell version is now `0.3.4` and capabilities include `relationship_memory_graph`, `relationship_memory_queries`, and `saas_ready_entity_relationship_edges`.

Manual examples:
- “Who is my fiancée?”
- “How is Kenleigh related to me?”
- “What dogs do I have?”
- “What relationships do you remember?”
- “Who works on Jarvis?”

Current status after 0.3.4:
- Memory has long-term facts, short-term facts, chat archive, memory candidates, scalable entity records, aliases/merge corrections, and relationship graph queries.
- Typed interface parity from 0.3.3a should remain intact.

Recommended next milestone:
- `0.3.5 Memory Preferences / Auto-Remember Controls`, allowing users/SaaS tenants to control what Jarvis may remember automatically, what requires approval, and what should never be stored.

## 0.3.4a Entity Phonetic Alias + Relationship Label Hotfix

This hotfix follows 0.3.4 Relationship Memory Graph.

Live testing showed that Jarvis could miss relationship lookups when the saved memory used one spelling of fiancé/fiancée and the query used another. It also showed that STT often hears `Kenleigh` as `Ken Lee`.

Changes:
- Normalized relationship labels across `fiance`, `fiancee`, `fiancé`, and `fiancée` to canonical `fiancée`.
- Added conservative phonetic aliases for person names, including patterns like `Kenleigh`, `Ken Lee`, `Ken Leigh`, and `Kenley`.
- Person records now automatically get those aliases for matching/search.
- Existing loaded person records are backfilled with phonetic aliases and normalized relationship edges.
- Entity merge now makes the target phrase canonical even when it resolves to the same record via alias, so `Ken Lee and Kenleigh are the same person` correctly displays `Kenleigh` afterward.
- Added regression tests in `tests/unit/test_memory_entity_phonetic_relationship_034a.py`.

Validation:
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 386 tests in 5.319s — OK`

Notes:
- App-shell version remains `0.3.4` to keep existing version-pinned tests stable, while the patch package itself is `0.3.4a`.
- This is not a full STT custom vocabulary feature. It makes memory tolerant after STT produces common variants. A future voice/STT update can add custom vocabulary/name biasing.

Next recommended options:
- Commit 0.3.4a after manual testing.
- Then continue memory with auto-remember controls, or do a dedicated STT custom vocabulary/name-bias patch to improve recognition before routing.

## 0.3.4b Relationship Display Cleanup Hotfix

This hotfix keeps the 0.3.4 relationship graph and 0.3.4a phonetic alias work intact, and only fixes relationship display/normalization issues discovered during live testing.

Changes:
- Relationship attributes that were accidentally merged into list-like values such as `["fiance fiancee", "fiancée"]` are normalized back into one clean display label.
- Jarvis should no longer say bracket/list formatting in natural memory answers, such as `your ['fiance fiancee', 'fiancée']`.
- `fiance`, `fiancee`, `fiancé`, `fiancée`, and merged strings like `fiance fiancee` normalize to `fiancée` before display.
- Existing loaded entity memories are cleaned in memory at load time so old records display naturally after restart.
- Entity prompt facts also sanitize relationship values before they are sent to the LLM humanizer.

Current status:
- Entity phonetic aliases are working for Kenleigh / Ken Lee style STT mistakes.
- Relationship graph queries are working, but continue testing real-world speech variants before expanding further.
- Next recommended memory update: memory preferences and auto-remember controls, or STT vocabulary/name biasing for frequently misheard personal names.
