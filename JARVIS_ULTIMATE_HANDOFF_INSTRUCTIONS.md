# Jarvis Ultimate Handoff Instructions

This file exists so a future ChatGPT project chat can quickly understand the current state of Jarvis Ultimate and continue without losing momentum.

## Current project status

Current committed milestone before this patch: **0.3.8c4 — Release-Safe Panel Geometry Freeze Hotfix**

Current patch milestone: **0.3.8d — Save Custom Layout Preset**

Versioning rule: after `0.2.9`, use `0.3.0`, not `0.2.10`. Current working version is `0.3.8d`. Hotfixes may use suffixes like `0.3.2a`.

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

## 0.3.5 Memory Preferences + Auto-Remember Controls

This milestone adds user-controlled memory policy rules so Jarvis can decide whether possible memories should be saved automatically, queued for review, kept temporarily, or blocked.

Changes:
- Added `MemoryPreferenceStore` at `src/jarvis/memory/preferences.py`.
- Added category-based policies: `auto`, `ask`, `short_term`, and `never`.
- Added memory preference commands such as `Show my memory preferences`, `Remember project rules automatically`, `Ask me before remembering people`, `Never remember financial information`, and `Keep daily life temporary`.
- Auto-capture now checks memory preferences before saving long-term memory, short-term memory, or memory candidates.
- Future screen-aware setting saves are policy-ready with categories like `app_settings`, `game_settings`, and `screen_context`.
- Sensitive categories such as financial data and secrets default to `never` for automatic saving.

Validation:
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 397 tests in 5.600s — OK`

## 0.3.5a Sensitive Memory Vault Routing Foundation

This hotfix follows 0.3.5 before committing the memory preference work. It keeps normal memory safe while preparing a future local encrypted Secure Vault / Password Manager Agent.

Changes:
- Added `SecureVaultStore` at `src/jarvis/memory/secure_vault.py`.
- Added sensitive-memory classification for passwords, API keys, access tokens, recovery codes, private keys, Wi-Fi passwords, and financial/account data.
- Explicit sensitive save requests are routed away from normal memory and into the secure-vault path.
- Because encrypted local vault storage is not implemented/enabled yet, Jarvis does not store raw secret values. He responds that secure vault routing is ready but encrypted storage is not enabled yet.
- Normal memory, entity memory, short-term memory, chat archive summaries, and memory candidates should not receive raw secrets through this route.
- Added secure vault status support and app-shell snapshot status.
- Added config fields for future vault enablement: `memory_secure_vault_enabled`, `memory_secure_vault_path`, and `memory_secure_vault_encrypted_storage_ready`.
- App shell capabilities now include `sensitive_memory_secure_vault_routing`, `password_manager_agent_foundation`, and `normal_memory_secret_blocking`.
- App shell version is now `0.3.5a`.

Manual examples:
- `Remember that my password is hunter2.` should not save to normal memory and should say encrypted vault storage is not enabled yet.
- `Remember that my bank account number is 123456789.` should route to the vault path and not long-term memory.
- `Secure vault status.` should explain that vault routing is ready but encrypted vault storage is not enabled yet.

Current status after 0.3.5a:
- Jarvis has safe policy controls for normal memory.
- Jarvis has routing foundations for a future Password Manager / Secure Vault Agent.
- Full encrypted vault storage is not implemented yet and should be treated as a future dedicated security feature.

Validation:
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 405 tests in 5.385s — OK`

Next recommended update:
- Commit 0.3.5 + 0.3.5a together after manual testing.
- Then continue with `0.3.6 Memory Review Dashboard / Cleanup Commands`, or start a dedicated `Secure Vault Agent` milestone if password-manager behavior becomes the priority.

## 0.3.6 Sensitive Chat Redaction + Memory Log Hygiene

This milestone closed the security gap where fake sensitive values could still appear in local chat/log files after secure-vault routing rejected them from normal memory.

Changes:
- Added sensitive redaction before writing normal chat archives, memory candidates, short-term metadata, app-shell UI history, voice session snapshots, and JSONL logs.
- Added installer cleanup for existing local files under `data/memory/chat_archive`, `data/memory/*.json`, `data/conversations`, and `logs`.
- Passwords, PINs, API keys, tokens, recovery codes, private keys, Wi-Fi passwords, bank/account/card numbers, and similar values should be replaced with redacted placeholders in normal files.
- Secure values still route to the future secure-vault path and are not saved to normal memory.

Validation:
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 413 tests in 6.873s — OK`

Current status after 0.3.6:
- Memory preferences and secure-vault routing are committed.
- Sensitive values are no longer left raw in normal local chat/log surfaces.
- Future secure vault/password-manager work should remain separate from normal memory.

## 0.3.7 Memory Review Panel + Spoken Summary Control

This milestone adds a visual memory-review layer. When the user asks Jarvis to show everything he remembers about someone or something, Jarvis now gives a short spoken response and opens a Memory Review card/panel with ranked bullet points.

Changes:
- Added `src/jarvis/memory/review.py` for ranked memory review payloads.
- Added a `memory_review` panel type to the UI panel registry.
- Added app-shell renderer support for Memory Review cards with ranked bullet lists.
- Added Memory Agent routing for commands like `Show everything you remember about Kenleigh` and `Open memory review for Jarvis`.
- Detailed reviews combine entity memory, relationship graph data, long-term memory, and short-term facts.
- Jarvis only speaks the short confirmation by default: `Here is everything I know about Kenleigh, sir.`
- Jarvis only reads the full review aloud if the user asks to `speak`, `read`, or `tell` everything.
- Memory review payloads preserve sensitive redaction.
- App shell version is now `0.3.7`.

Validation:
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 419 tests in 6.452s — OK`

Next recommended update:
- After committing 0.3.7, continue with memory edit/cleanup commands: edit a specific memory, forget everything about an entity/topic, clean duplicate memories, and show recent memory changes.


## 0.3.8 — Dockable Workspace Panels

Changes:
- Added draggable and resizable app-shell panels.
- Added local persistent panel layout storage.
- Added layout lock/unlock, layout reset, and layout presets for Gaming/Coding/Music/Minimal.
- Added panel command input for opening panels quickly.
- Added first panel popout support for moving panels to another monitor.
- Kept memory review cleanup from 0.3.7a.

Status:
- UI workspace is ready for Tanner to manually test.
- Known future improvement: make popout windows fully interactive and backed by dedicated Electron BrowserWindows instead of first-pass mirrored popouts.

Next recommended step:
- After testing/commit, continue UI polish with dedicated Electron popout window management or return to memory review edit/delete commands.

## 0.3.8a — Panel Lock Only

This milestone starts the safer post-reset UI stabilization path. It intentionally changes only one thing: per-panel locking.

Changes:
- Added a per-panel **Lock** button beside the existing **Min**, **Dock**, and **Pop** panel controls.
- Added persistent local storage for individual panel lock states.
- Locked panels cannot be dragged or resized while the global layout is unlocked.
- Unlocked panels continue to drag and resize as before.
- The global layout lock still works the same way as before.
- Added tests for the new app-shell version/capability, renderer lock storage/action, and locked-state CSS.
- App shell version is now `0.3.8a`.

Validation:
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 427 tests in 4.450s — OK`

Current status after 0.3.8a:
- Jarvis is still on the reset 0.3.8 dockable workspace baseline.
- Panel locking is available for manual testing without touching fragile popout, preset, or responsive layout behavior.

Next recommended update:
- `0.3.8b — Safer Drag/Resize Containment`, focused only on panel minimum sizes, header/control containment, and preventing panel content from spilling behind buttons.
- Keep dropdown text color, save custom preset, responsive resize scaling, and real Electron popout windows as separate later patches.

## 0.3.8b — Panel Header Containment + First Drag Stabilization

This hotfix follows live testing of 0.3.8a. It keeps the reset 0.3.8 dockable workspace baseline and the 0.3.8a per-panel Lock button, but fixes the two visible layout problems from manual testing.

Changes:
- Panel header action buttons now wrap safely instead of overlapping each other or the panel title.
- Left-rail panels use a safer stacked header layout so Hide/Lock/Min/Dock/Pop stay visible.
- The Lock button no longer expands from `Lock` to `Locked`, reducing header width pressure while still showing active state through color/border styling.
- Layout preset dropdown options now have explicit dark background and readable text in Electron/Windows menus.
- First drag/resize of a docked panel now uses an invisible placeholder so nearby panels do not suddenly expand or jump while the dragged panel is being promoted to floating mode.
- Drag/resize now promotes the active panel to floating without reapplying the entire layout during pointer-down.
- App shell version is now `0.3.8b` and capabilities include `panel_header_no_overlap_guard` and `panel_drag_placeholder_stabilization`.

Validation:
- `node --check app_shell/renderer/renderer.js`
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 430 tests in 4.883s — OK`

Manual testing focus:
- Runtime and Workspace headers should not have overlapping buttons.
- Dragging a docked left-rail panel for the first time should not make the surrounding panels balloon or stack on top of each other during the drag.
- Locked panels should still refuse drag and resize.

Next recommended update:
- Continue with the remaining small UI fixes one at a time: responsive window resize scaling, Save Custom Preset, then real Electron popout windows.

## 0.3.8c — Responsive Window Resize

This focused UI stabilization patch follows the committed 0.3.8b checkpoint. It does not add new features; it makes the existing dockable/floating panel system safer when the Jarvis app window is minimized, restored, maximized, or resized.

Changes:
- Added viewport-aware layout bounds for floating panels.
- Floating panels are clamped inside the visible app window when the window size changes.
- Drag and resize completion now re-clamps the active panel before saving the layout.
- Window resize handling is debounced through `requestAnimationFrame` so Jarvis does not repeatedly reapply layout mid-resize.
- Resize handling waits until active drag/resize operations finish instead of fighting the pointer movement.
- Removed the older small-window rule that forced floating panels back into relative layout flow, because that could make panels jump during responsive transitions.
- Added responsive CSS guards for narrower/shorter windows while preserving the stable 0.3.8b panel header containment behavior.
- App shell version is now `0.3.8c` and capabilities include `responsive_panel_resize_clamping`, `floating_panel_viewport_bounds`, and `debounced_layout_resize_handler`.

Validation:
- `node --check app_shell/renderer/renderer.js`
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 433 tests in 5.139s — OK`

Manual testing focus:
- Open Jarvis, move a few panels, then maximize and restore the window.
- Shrink the app window and verify floating panels stay reachable instead of getting stuck off-screen.
- Drag and resize panels after a window resize and confirm buttons still do not overlap.
- Use Reset Layout and layout presets after resizing to verify the layout still feels stable.

Next recommended update:
- `0.3.8d — Save Custom Preset`, adding a button to save the current stable layout as a selectable preset. Keep real Electron popout windows and visual polish as later separate patches.

## 0.3.8c1 — Window State Panel Follow + Active Panel Priority Hotfix

This hotfix follows live testing of 0.3.8c. It keeps the stable 0.3.8b/0.3.8c dockable-panel behavior and only fixes the remaining responsive layout issues Tanner found while maximizing/restoring the Jarvis window and resizing panels.

Changes:
- Floating panel layouts now remember the viewport size they were saved against.
- When updating from older 0.3.8c saved layouts, Jarvis can infer an initial saved viewport from existing floating-panel coordinates.
- When the Jarvis window is maximized, restored, or resized, floating panels scale proportionally with the new viewport instead of staying stuck in the old window-size coordinates.
- Floating panels are still clamped inside the visible app window after scaling.
- The last active panel now gets visual priority: clicking, dragging, or resizing a panel brings it to the front using z-index tracking.
- Runtime and other floating panels now have safer minimum restored sizes.
- Runtime panel content is contained with scroll/word wrapping so long model names and status text should not spill outside when the panel is small.
- App shell version is now `0.3.8c1` and capabilities include `viewport_scaled_panel_restore`, `last_active_panel_z_order`, `floating_panel_content_containment`, and `runtime_panel_minimum_size_guard`.

Validation:
- `node --check app_shell/renderer/renderer.js`
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 437 tests in 3.635s — OK`

Manual testing focus:
- Move/resize a few panels, then maximize and restore Jarvis. Floating panels should follow the new window size instead of keeping the old layout coordinates.
- Click overlapping floating panels and verify the last clicked/moved panel comes to the front.
- Shrink the Runtime panel and verify its text stays contained instead of spilling outside the panel.
- Confirm Lock, Min, Dock, Pop, Reset Layout, and layout presets still work.

Next recommended update:
- If this hotfix passes manual testing, commit `0.3.8c1` and then continue to `0.3.8d — Save Custom Preset`.
- Keep real Electron popout windows and visual polish as later separate patches.

## 0.3.8c2 — Workspace Safe Scaling Hotfix

This hotfix follows `0.3.8c1` after live testing showed that panels could still overlap the top control panel when maximizing and restoring the Jarvis window.

Changes:
- Floating panels now scale inside the actual workspace safe area below the top control bar instead of the full app window.
- The panel viewport snapshot now tracks `left`, `top`, `width`, and `height` from `#interfaceGrid`.
- Maximize/restore scaling preserves relative panel position and size within that workspace area.
- Panels are clamped below the top controls so they should not cover the Native App Shell / Jarvis Ultimate header panel after restoring.
- The panel layout viewport storage key was moved to `jarvis.appShell.panelLayoutViewport.v038c2` so old full-window viewport snapshots do not keep causing bad scaling.
- App shell version is now `0.3.8c2` and capabilities include `workspace_safe_area_panel_scaling`, `maximize_restore_panel_ratio_preservation`, and `top_bar_overlap_prevention`.

Validation:
- `node --check app_shell/renderer/renderer.js`
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 440 tests in 3.516s — OK`

Manual testing focus:
- Move panels, maximize, restore, and confirm panels remain below the top control bar while keeping their relative positions and sizes.
- If old saved positions still look odd, use Reset Layout once and retest.

Next recommended step:
- Commit `0.3.8c2` after manual testing succeeds.
- Then continue to `0.3.8d — Save Custom Preset`, unless another tiny layout hotfix is needed first.


## 0.3.8c3 — Independent Panel Drag Freeze Hotfix

This hotfix follows `0.3.8c2` after live testing showed that moving the Core Orb panel could cause the Conversation panel to jump toward the center and appear behind the orb.

Changes:
- Added an active panel interaction guard so drag/resize operations only mutate the panel being moved.
- Captures a frozen snapshot of every unaffected panel before a drag/resize begins.
- Restores unaffected panel layout records when the drag/resize finishes, so moving the orb does not reflow or relocate the conversation panel.
- Skips full layout reapplication during active panel interactions, preventing bridge refreshes from re-sanitizing every panel mid-drag.
- Responsive resize clamping now waits while a panel interaction is active or settling.
- `applyPanelLayout` can preserve frozen panel keys when only the active panel should be updated.
- App shell version is now `0.3.8c3` and capabilities include `independent_panel_drag_freeze`, `active_panel_only_drag_updates`, and `no_neighbor_panel_reflow_on_drag`.

Validation:
- `node --check app_shell/renderer/renderer.js`
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 443 tests in 3.482s — OK`

Manual testing focus:
- Overlap or place the Core Orb and Conversation panels near each other.
- Drag only the Core Orb panel. The Conversation panel should not move, snap, resize, or go behind the orb unless you click/move it directly.
- Drag the Conversation panel next. The Core Orb panel should stay where it was.
- Test resize on one panel and confirm neighboring panels stay fixed.
- Re-test maximize/restore behavior from 0.3.8c2.

Next recommended step:
- Commit `0.3.8c3` if manual testing succeeds.
- Then continue to `0.3.8d — Save Custom Preset`, unless another small layout stability issue appears first.

## 0.3.8c4 — Release-Safe Panel Geometry Freeze Hotfix

This hotfix follows `0.3.8c3` after live testing showed that the Conversation panel could still move after releasing the Core Orb panel, even though it stayed put during the drag.

Changes:
- Unaffected panels are now frozen from their real on-screen DOM geometry before a drag/resize begins, not from possibly stale saved layout records.
- The frozen DOM geometry is applied immediately to unaffected panels so bridge refreshes, grid reflow, and release-time layout sanitizing cannot snap them somewhere else.
- `applyPanelLayout` no longer reintroduces stale floating geometry when preserving unaffected panels after a drag/resize.
- Moving the Core Orb panel should not cause the Conversation panel to snap after release.
- Resizing one panel should not cause another panel to move after release.
- App shell version is now `0.3.8c4` and capabilities include `dom_geometry_panel_freeze`, `post_drag_neighbor_snap_guard`, and `release_safe_panel_layout_restore`.

Validation:
- `node --check app_shell/renderer/renderer.js`
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 446 tests in 3.529s — OK`

Manual testing focus:
- Put the Core Orb and Conversation panels near each other.
- Drag the Core Orb panel and release it. The Conversation panel should stay exactly where it was before, during, and after release.
- Drag the Conversation panel and release it. The Core Orb panel should stay exactly where it was.
- Resize one panel and confirm no other panel moves when the mouse is released.
- Re-test maximize/restore once after Reset Layout if old saved positions still look strange.

Next recommended step:
- Commit `0.3.8c4` if manual testing succeeds.
- Then continue to `0.3.8d — Save Custom Preset`, unless another tiny layout stability issue appears first.


## 0.3.8d — Save Custom Layout Preset

This milestone follows `0.3.8c4` after the dockable workspace became stable enough to add the next planned feature: saving the current layout as a reusable preset.

Changes:
- Added a top-bar `Save Preset` button beside the layout preset selector.
- The button prompts for a preset name and stores the current panel layout locally in Electron/Chromium `localStorage`.
- Saved custom presets are appended under a `Custom` group in the existing Layouts dropdown.
- Custom presets preserve floating/docked state, panel size, panel position, minimized state, popped marker, and z-order metadata.
- Custom presets save the workspace viewport snapshot and scale back into the current workspace area when applied, so presets can survive maximize/restore and normal window-size changes.
- Re-saving with the same name asks before overwriting the existing custom preset.
- The feature does not change the recent `0.3.8c4` drag/release geometry freeze behavior.
- App shell version is now `0.3.8d` and capabilities include `custom_workspace_layout_presets`, `user_saved_layout_preset_button`, and `viewport_scaled_custom_layout_restore`.

Validation:
- `node --check app_shell/renderer/renderer.js`
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 450 tests in 3.484s — OK`

Manual testing focus:
- Arrange panels into a layout you like.
- Click `Save Preset`, give it a name, and confirm it appears under the `Custom` section of the Layouts dropdown.
- Move panels around or apply a built-in preset.
- Select the custom preset and confirm the saved layout comes back.
- Maximize/restore the window and apply the custom preset again to confirm it scales into the workspace instead of covering the top bar.
- Confirm dragging one panel still does not move another panel.

Next recommended step:
- Commit `0.3.8d` after manual testing succeeds.
- Then continue to `0.3.8e — Real Pop-Out Windows`, or do a small visual polish pass only if the saved preset feature is stable.


## 0.3.8d1 — Secure Vault Version Test Alignment Hotfix

This hotfix follows `0.3.8d` after live testing showed one unit test still expected the previous app-shell version `0.3.8c4` even though the runtime correctly reports `0.3.8d`.

Changes:
- Updated `tests/unit/test_memory_secure_vault_035a.py` so its version assertion expects `0.3.8d`.
- No runtime behavior changed.
- No UI behavior changed.
- No app-shell version bump; the active runtime remains `0.3.8d`.
- This only fixes test-suite alignment after the Save Custom Layout Preset patch.

Validation:
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 450 tests in 3.618s — OK`

Manual testing focus:
- No new manual UI behavior is included in this hotfix.
- Re-run the full unit test suite.
- Then start Jarvis and continue manually testing the Save Preset workflow from `0.3.8d`.

Next recommended step:
- Commit `0.3.8d` and this `0.3.8d1` test-alignment hotfix together once tests pass.
- Then continue to `0.3.8e — Real Pop-Out Windows`, or pause for a small visual polish pass if needed.

## 0.3.8d2 — Save Preset Name Dialog Hotfix

This hotfix follows `0.3.8d` after live testing showed that clicking `Save Preset` could save the layout behavior internally without showing a visible naming prompt in the Electron app shell.

Root cause:
- The first save-preset implementation relied on the browser-native `window.prompt()` dialog.
- In the Electron app shell this prompt can be unavailable, hidden, or not reliably visible to the user, making the save look like nothing happened and preventing the user from naming the preset.

Changes:
- Added an in-shell custom modal dialog for naming saved layout presets.
- The `Save Preset` button now opens a visible Jarvis-styled dialog with a preset-name input, Cancel button, and Save Preset confirmation button.
- The dialog supports Enter to save, Escape/backdrop click to cancel, and auto-focuses/selects the suggested name.
- The saved preset still appears under the `Custom` group in the Layouts dropdown.
- Existing custom preset storage, workspace viewport scaling, panel z-order, and 0.3.8c4 drag/release stability remain intact.
- No app-shell version bump; active runtime remains `0.3.8d` so version-pinned tests remain stable.
- Capabilities now include `custom_layout_preset_name_dialog` and `electron_safe_custom_preset_naming`.

Validation:
- `node --check app_shell/renderer/renderer.js`
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 454 tests in 4.479s — OK`

Manual testing focus:
- Click `Save Preset` and confirm the visible naming dialog opens.
- Type a custom name and save it.
- Confirm the named preset appears under `Custom` in the Layouts dropdown.
- Move panels around, choose the custom preset, and confirm the saved layout restores.
- Try Cancel/Escape and confirm no unwanted preset is saved.

Next recommended step:
- Commit `0.3.8d`, `0.3.8d1`, and `0.3.8d2` together after manual testing succeeds.
- Then continue to `0.3.8e — Real Pop-Out Windows`, or do a small visual polish pass if save presets and panel layout stability are now reliable.
