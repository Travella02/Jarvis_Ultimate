# Jarvis Ultimate Handoff Instructions

This file exists so a future ChatGPT project chat can quickly understand the current state of Jarvis Ultimate and continue without losing momentum.

## Current project status

Current committed milestone before this patch: **0.2.9 — Always-On Memory Tiers + Chat Archive Foundation**

Current patch milestone: **0.3.0 — Memory Auto-Capture + Candidate Review**

Versioning rule: after `0.2.9`, use `0.3.0`, not `0.2.10`. Hotfixes may use suffixes like `0.3.0a`.

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
- always-on memory foundation.

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
- reject candidate memories.

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
- Future memory should include safer auto-promotion rules, entity memory, people/pets/projects/apps/places, and eventually face identity memory.

## Next recommended update

Recommended next milestone: **0.3.1 Memory Candidate Review Polish + Auto-Promotion Rules** or **0.3.1 Entity Memory Foundation**.

Recommended goals:

- make candidate review responses more conversational after real testing,
- add “remember things like this automatically” / “do not remember things like this” controls,
- add safer high-confidence auto-promotion rules,
- add entity memory schema for people, pets, apps, projects, places, and relationships,
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
- Next recommended update after committing 0.3.0: `0.3.1 Entity Memory Foundation` or memory auto-promotion tuning.
