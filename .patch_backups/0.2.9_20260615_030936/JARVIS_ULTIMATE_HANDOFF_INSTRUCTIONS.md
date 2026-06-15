# Jarvis Ultimate Handoff Instructions

## Purpose
This file exists so a future ChatGPT/Jarvis development chat can immediately understand the current project state, patch rules, user preferences, and the next recommended step. Update this file with every Jarvis patch.

## Current Version
**0.2.8 - Memory Pipeline Foundation + humanized memory responses**

## Current Status
Jarvis Ultimate is a local-first desktop assistant project with:

- Native Electron app shell using HTML/CSS/JavaScript
- Python local API bridge
- LM Studio local LLM integration
- Faster Whisper STT
- Kokoro TTS
- Always-on sleep/wake voice mode
- 3D orb interface with state changes
- App Agent with app open/close/focus, launch verification, aliases, and default roles
- Ability registry foundation
- Short-term conversation memory
- New long-term memory pipeline foundation with humanized memory recall responses

## User Patch Rules
Always follow these rules for Jarvis updates:

1. Do not paste large code directly in chat.
2. Deliver downloadable patch zip files.
3. Include an installer script named like `apply_<version>_..._patch.py`.
4. Include a `patch_files/` folder.
5. Include patch notes and a testing guide inside the patch package.
6. Write the apply/test/cleanup/commit steps directly in chat.
7. Run the full test suite before delivery:
   ```powershell
   python -m unittest discover -s tests -v
   ```
8. Do not include README files outside `patch_files/` in the patch package.
9. Do not include `START_HERE` files in the patch package.
10. Include and update this `JARVIS_ULTIMATE_HANDOFF_INSTRUCTIONS.md` file with every patch.
11. Unit tests must never open or close real apps.
12. Keep natural-language commands routed through Jarvis/agents; slash commands may bypass when explicitly designed.

## Recent Completed Work

### 0.2.3 - Smart App Discovery and Voice Readback
- App Agent can discover apps, remember aliases/paths, close apps, and speak tool responses.
- Added test-safe dry-run behavior so unit tests do not open apps.
- Added taskkill fallback for app closing.
- Upgraded Faster Whisper default config to `medium.en`, `auto`, `auto`.

### 0.2.4 - App Discovery Speed and Router Polish
- Improved known app resolution and background indexing.
- Added Snipping Tool aliases.
- Fixed thinking state purple/violet visual.

### 0.2.5 - App Discovery Speed and Caption Sync
- Improved Discord/Spotify launch matching.
- Caption under orb now starts while Jarvis speaks for short tool responses.

### 0.2.6 - App Agent Reliability and Launch Verification
- Added app launch verification.
- Added stale launcher recovery.
- Added manual alias teaching such as “when I say music, open Spotify”.
- Fixed chat scroll snapping behavior.

### 0.2.7 - App Alias Management and Default Roles
- Multiple aliases per app.
- Default roles like browser/music/editor.
- List, forget, and rename aliases.
- Focus/switch app behavior.
- Learned aliases and roles beat generic app discovery.

### 0.2.8 - Memory Pipeline Foundation
- Added local JSON-backed long-term memory store.
- Memory Agent can save, search, list, and forget memories.
- Long-term memory can be injected into LLM context when relevant.
- Added memory config settings.
- App shell runtime snapshot includes memory status.
- Hotfix: Memory recall/search responses are now humanized instead of database-style output.

## Current Architecture Notes
Jarvis should keep using specialized agents:

- App Agent: apps/windows only
- Memory Agent: saved context only
- File Agent: files/folders only
- Routine Agent later: multi-step workflows that call other agents
- Screen Agent later: OCR/screen awareness
- Recorder Agent later: clips/recording
- Weather/Web agents later: external info

Avoid turning one agent into a giant general-purpose tool. Keep agents small and specialized.

## Next Recommended Step
After committing 0.2.8, move to:

**0.3.0 File Agent Foundation**

Recommended goals:

- Find files and folders by name
- Open files and folders safely
- Search inside the Jarvis project
- Read/summarize safe text files
- Confirmation required for write/move/delete actions
- UI action cards for file results

## Important User Preferences
- User wants Jarvis to call him “sir.”
- User wants Jarvis to feel like a real assistant, not a program announcing implementation details.
- User prefers direct, practical patch instructions in chat.
- User likes installer scripts with `patch_files/`.
- User wants the UI to stay dark, holographic, orb-centered, and desktop-app based.
- User wants aliases/default roles to be user-specific and SaaS-ready.
- User wants Memory to become the central pipeline that makes future agents smarter.
