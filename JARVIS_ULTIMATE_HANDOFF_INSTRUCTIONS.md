# Jarvis Ultimate Handoff Instructions

This file exists so a future ChatGPT project chat can quickly understand the current state of Jarvis Ultimate and continue without losing momentum.

## Current project status

Current committed milestone: **0.2.9 — Always-On Memory Tiers + Chat Archive Foundation**

The latest requested task after 0.2.9 was to update `README.md` so the project can be made public on GitHub for job-search/portfolio purposes.

Next planned main milestone: **0.3.0 — Memory Auto-Capture + Candidate Review**

Versioning rule: after `0.2.9`, use `0.3.0`, not `0.2.10`. Hotfixes may use suffixes like `0.2.9a`.

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
- early File Agent foundation/placeholders,
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
- incremental always-on memory persistence.

Known memory design goals:

- Jarvis will eventually run for weeks or months at a time.
- Do not rely on restarts for memory processing or cleanup.
- Memory should persist incrementally while running.
- Future memory should include automatic memory candidate detection, candidate review, promotion/rejection, entity memory, people/pets/projects/apps/places, and eventually face identity memory.

## Next recommended update

**0.3.0 Memory Auto-Capture + Candidate Review**

Recommended goals:

- add candidate memory queue,
- auto-save useful short-term context,
- score candidate memories by importance,
- add review commands:
  - “what memories are waiting for review?”
  - “save that permanently”
  - “forget that candidate”
  - “promote that to long-term memory”
- keep sensitive/private memory behavior user-controlled,
- keep everything local-first and always-on safe.

## Public GitHub README update

A new public-facing `README.md` was created to present Jarvis Ultimate as a portfolio/job-search project. It explains:

- project purpose,
- current capabilities,
- architecture,
- setup,
- testing,
- privacy/local data handling,
- version history,
- roadmap,
- recruiter/reviewer notes.

