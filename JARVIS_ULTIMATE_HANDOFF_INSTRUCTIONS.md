# Jarvis Ultimate Handoff Instructions

## Current Version

**0.2.9 — Always-On Memory Tiers + Chat Archive Foundation**

Latest hotfix applied in this chat: **0.2.9b — Memory Response De-Dupe + Chat Scroll Comfort**

Jarvis Ultimate is a local-first desktop assistant project with a native Electron app shell, voice bridge, Jarvis orb UI, App Agent, and foundational memory pipeline.

## Standing Patch Rules

- Provide downloadable patch zip packages, not pasted code.
- Include an installer script named like `apply_<version>_<description>_patch.py`.
- Include all replacement files inside `patch_files/`.
- Do not include README files outside `patch_files/`.
- Do not include `START_HERE` files.
- Include patch notes and a testing guide inside `patch_files/`.
- Explain the apply steps directly in chat every time.
- Run the full test suite before delivery:
  `python -m unittest discover -s tests -v`
- Include the tested result in the delivery message.
- For future Jarvis versions, after `0.2.9`, the next main version is `0.3.0`, not `0.2.10`.
- Update this handoff file with every patch.

## Project Direction

Jarvis is intended to be an always-on assistant that can stay running for weeks or months at a time. Future versions will control security systems, cameras, screen awareness, routines, and other long-running services. Do not rely on restarts for memory flushing, cleanup, indexing, or persistence.

Memory and runtime systems should use:

- incremental saves
- crash-safe writes
- daily log/archive files
- background or uptime-safe maintenance
- bounded in-memory buffers
- retention and rotation policies
- explicit user control for saved memories

## Current Core Capabilities

### Native App Shell / UI

- Electron desktop app shell, not browser-based.
- HTML/CSS/JS Jarvis orb interface.
- Orb-only mode.
- Holographic dark UI.
- Smooth state animations for sleeping, listening, thinking, speaking, and error.
- Speech captions under the orb, synced while Jarvis speaks.
- Hide/show panels.
- Chat panel no longer forces scroll while manually reading older messages.

### Voice

- Faster Whisper STT.
- Kokoro TTS.
- Sleep/wake mode auto-starts after warmup.
- Wake phrases include “Jarvis,” “Hey Jarvis,” and similar.
- Sleep phrases include “that’s all Jarvis” and natural thank-you endings.
- Jarvis should address the user as “sir.”

### App Agent

The App Agent is solid enough to pause for now.

It supports:

- opening apps
- closing apps with safe taskkill fallback
- focusing/switching to already-open apps
- app launch verification
- learned app aliases
- multiple aliases per app
- default app roles like browser/music/editor
- listing aliases
- forgetting aliases/nicknames/names/app names
- routing phrases like “when I say music or jams, open Spotify”
- prioritizing learned aliases over broad discovery

Future App Agent improvements can include window resizing/moving/minimizing, but those can wait.

### Memory Pipeline

0.2.8 added explicit long-term memory.

0.2.9 adds always-on memory tiers:

- rolling short-term conversation memory for current context
- short-term fact memory that lasts a few days
- permanent long-term memory
- daily chat archive memory saved as JSONL
- memory maintenance foundation
- crash-safe JSON writes for memory tier files
- chat archive search commands
- temporary memory commands

Important memory files:

- `data/memory/long_term_memory.json`
- `data/memory/short_term_memory.json`
- `data/memory/chat_archive/YYYY-MM-DD.jsonl`
- `data/memory/maintenance_status.json`

## Latest Update Summary — 0.2.9 / 0.2.9a / 0.2.9b

0.2.9 added:

- `src/jarvis/memory/always_on.py`
- `ShortTermFactStore`
- `ChatArchiveStore`
- `MemoryMaintenance`
- config options for short-term fact memory and chat archive memory
- daily chat archive persistence for every handled command
- temporary memory commands such as “remember this for a few days”
- chat archive search phrases such as “what did we talk about…”
- memory tier status in runtime/app-shell snapshots
- tests for memory tiers and chat archive persistence

0.2.9a hotfix improved:

- memory search responses so they sound human instead of like database dumps
- chat archive responses so they summarize naturally instead of listing raw `You:` / `Jarvis:` turns
- memory status responses so they hide raw file paths and read more naturally
- long-term memory configuration so `0` means no fixed record cap
- project defaults so long-term memory is not artificially capped at 500 records

0.2.9b hotfix improved:

- memory search de-duplication so partial matches like “your favorite test color” do not repeat beside the full fact
- chat archive responses so they stay short and conversational instead of reading long transcript excerpts
- chat panel scrolling so manual scrolling is not pulled back to the newest message while the user is reading

## Next Recommended Step

The next major version should be:

**0.3.0 — File Agent Foundation**

Suggested 0.3.0 goals:

- find files by name
- open files
- open folders
- search the Jarvis project
- summarize project files
- list recent project files
- use confirmation for write/delete/move operations
- connect file operations to memory where useful

Memory roadmap after 0.3.0:

- automatic memory candidate detection
- memory review queue
- promotion from short-term to long-term
- entity memory for people, pets, places, apps, and projects
- face/person memory integration when vision is added
- semantic/vector search later

## User Preferences To Preserve

- The user prefers patch zips with installer scripts and `patch_files/`.
- The user does not want code pasted into chat.
- Apply steps should be written directly in chat.
- Patch notes and testing guides must be included.
- No README or START_HERE files outside patch files.
- Jarvis should call the user “sir.”
- Jarvis should be local-first and always-on.
- Natural speech should route through the LLM/agent system; slash commands may bypass.
- UI should feel like a real Jarvis interface, not a browser or demo dashboard.


## Latest Hotfix: 0.2.9c Memory Chat Archive Test Compatibility

- 0.2.9c is a small hotfix on top of the uncommitted 0.2.9 memory update.
- It keeps the 0.2.9b shorter chat archive summaries, but makes the wording start naturally with “I remember…” so existing humanization tests and Jarvis tone expectations both match.
- It keeps chat archive replies short and avoids transcript dumps.
- Current commit target remains: `0.2.9 Add always-on memory tiers and chat archive`.
- After 0.2.9 is committed, the next main version should be `0.3.0`, not `0.2.10`.

## Latest Hotfix: 0.2.9d LLM Chat Archive Summary

- 0.2.9d is a small hotfix on top of the uncommitted 0.2.9 memory update.
- It changes chat archive search answers so Jarvis uses the attached local LLM to summarize relevant chat archive turns when available.
- The chat archive remains the evidence source, but the LLM turns that evidence into a short, natural spoken answer instead of Jarvis stitching together awkward log fragments.
- If the LLM is unavailable, Jarvis falls back to a safer deterministic summary that stays short and avoids raw transcript dumps.
- It also keeps memory response de-duplication behavior so partial facts do not repeat beside complete facts.
- Current commit target remains: `0.2.9 Add always-on memory tiers and chat archive`.
- After 0.2.9 is committed, the next main version should be `0.3.0`, not `0.2.10`.
