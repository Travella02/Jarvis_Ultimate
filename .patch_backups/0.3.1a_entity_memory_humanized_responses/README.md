# Jarvis Ultimate

**Jarvis Ultimate** is a local-first desktop AI assistant built to feel like a persistent operating-system companion rather than a chatbot in a browser. The project combines a native desktop interface, voice interaction, local LLM routing, modular agents, app control, and an always-on memory pipeline.

This repository is an active personal AI-assistant build. The goal is to create a modular assistant that can eventually control desktop apps, remember useful context over time, support voice-first workflows, connect to future vision/security systems, and run continuously as a long-lived local service.

> Current milestone: **0.3.1 — Scalable Entity Memory Foundation**  
> Next planned milestone: **0.3.2 — Entity Memory Polish / Memory Auto-Promotion Controls**

---

## Why this project exists

Jarvis Ultimate is being built as a practical, local-first assistant that can grow one ability at a time. Instead of building a single large script that does everything, the project is organized around specialized agents and a central runtime so new capabilities can be added safely and tested independently.

The long-term vision is for Jarvis to:

- stay running for long periods of time without relying on restarts,
- listen through a sleep/wake voice loop,
- use a local LLM as the reasoning layer,
- control desktop apps and files,
- remember useful information over time,
- eventually connect to screen/camera awareness,
- eventually support routines, security-system control, and other always-on automation tasks.

---

## Current capabilities

### Native desktop app shell

Jarvis opens as a desktop application instead of a browser tab. The UI is built with an Electron app shell and communicates with the Python backend through a local bridge API.

Current UI features include:

- animated Jarvis orb interface,
- sleep/listening/thinking/speaking/error visual states,
- voice status and warmup indicators,
- conversation panel,
- workspace/action-card area,
- diagnostics drawer,
- orb-only mode,
- speech caption text under the orb while Jarvis speaks.

### Voice-first interaction

Jarvis is designed around voice interaction with sleep/wake behavior.

Current voice features include:

- wake phrase listening,
- listen-once mode,
- spoken responses through TTS,
- speech-to-text through Faster Whisper,
- configurable STT model/device settings,
- voice warmup before conversation,
- automatic return to sleep/wake mode.

### Local LLM integration

Jarvis is designed to use a local model through LM Studio or a compatible local API. The LLM handles natural conversation and increasingly helps with summarization and memory workflows.

Current LLM-related features include:

- local LLM provider configuration,
- natural conversation fallback,
- LLM-assisted chat archive summarization,
- memory context injection when relevant.

### Structured entity memory

Jarvis now has a structured entity-memory layer beside plain long-term and short-term memories. Entity memory is built for the future SaaS version because it uses a registry-driven schema instead of hardcoded one-off records.

Current default entity types include:

- user,
- person,
- pet,
- project,
- app,
- place,
- device,
- vehicle,
- organization.

The entity registry can add future types such as workspace, subscription, customer, ticket, team, routine, or asset without changing the core storage schema.

### Modular agent system

Jarvis is built around specialized agents. Each agent owns a specific domain instead of turning the project into one large monolithic assistant.

Current registered agent areas include:

- App Agent,
- Memory Agent,
- File Agent placeholder/foundation,
- Conversation Agent,
- Avatar/UI Agent,
- Voice-related runtime pieces,
- other developing system agents.

The goal is for future agents to plug into shared routing, memory, safety, and UI systems.

### App Agent

The App Agent is the most developed ability so far. It allows Jarvis to control desktop applications in a user-friendly way.

Current App Agent features include:

- open apps,
- close apps,
- focus/switch to already-running apps,
- launch verification,
- taskkill fallback for closing apps on Windows,
- app discovery and caching,
- learned aliases,
- multiple aliases per app,
- default app roles such as browser/music/editor,
- list/forget/change aliases,
- user-specific naming such as “when I say music, open Spotify.”

Example commands:

```text
Jarvis, open Chrome.
Jarvis, close Chrome.
Jarvis, switch to VS Code.
Jarvis, when I say music or jams, open Spotify.
Jarvis, open music.
Jarvis, forget the nickname jams.
Jarvis, use Microsoft Edge as my main browser.
Jarvis, open browser.
```

### Memory pipeline

Jarvis now has the first real memory foundation. Memory is designed for an always-on assistant that may run for weeks or months at a time.

Current memory features include:

- explicit long-term memory saves,
- short-term memory with expiration,
- daily chat archive files,
- crash-safe JSON writes,
- memory status commands,
- memory search commands,
- chat archive search,
- LLM-based chat archive summarization,
- automatic memory candidate capture,
- candidate review queue,
- approve/promote/reject candidate memories,
- automatic short-term memory capture for recent context,
- structured entity memory for people/pets/projects/apps/places/devices/vehicles/organizations,
- scalable entity type registry for future SaaS memory categories,
- handoff file that tracks project status for future development sessions.

Example commands:

```text
Jarvis, remember that my favorite color is blue.
Jarvis, what do you remember about my favorite color?
Jarvis, remember this for a few days.
Jarvis, what did we talk about memory?
Jarvis, memory status.
Jarvis, remember that Kenleigh is my fiancée.
Jarvis, who is Kenleigh?
Jarvis, list remembered pets.
```

---

## Architecture overview

Jarvis Ultimate is split into a Python backend and a desktop app shell.

```text
Jarvis_Ultimate/
├─ app_shell/                 # Electron desktop UI
├─ src/                       # Python backend/runtime/agents
├─ scripts/                   # Launch scripts and helpers
├─ tests/                     # Unit tests
├─ data/                      # Local runtime data, cache, memory stores
├─ config/                    # Configuration files
├─ assets/                    # UI/assets/resources
└─ JARVIS_ULTIMATE_HANDOFF_INSTRUCTIONS.md
```

### High-level flow

```text
User voice/text input
        ↓
Voice/STT or app-shell input
        ↓
Jarvis runtime/router
        ↓
Agent selection or LLM conversation
        ↓
Specialized agent action
        ↓
Memory/logging/UI event updates
        ↓
TTS response + app-shell caption output
```

### Design principles

- **Local-first:** Prioritize local models, local memory, and local user control.
- **Modular agents:** Each ability should live in a specialized agent.
- **Always-on safe:** Memory and logging must persist incrementally without requiring restarts.
- **Human-feeling interaction:** Responses should sound natural, not like database dumps.
- **Tested patches:** Every update should include tests and a user-facing testing guide.
- **SaaS-aware structure:** User-specific aliases, preferences, memory, and device paths should be separated so the system can evolve toward a multi-user product later.

---

## Tech stack

### Backend

- Python
- Local runtime/agent architecture
- Local API bridge for app-shell communication
- JSON/JSONL local persistence for early memory and cache systems
- `unittest` test suite

### UI

- Electron
- HTML/CSS/JavaScript
- Native desktop app shell
- Animated orb interface
- Local bridge polling/events

### AI/voice

- LM Studio-compatible local LLM provider
- Faster Whisper for speech-to-text
- Kokoro TTS for speech output
- Local-first voice pipeline

---

## Setup

This project is still in active development. Exact setup can change between milestones, but the current workflow is:

### 1. Clone the repository

```powershell
git clone <your-repo-url>
cd Jarvis_Ultimate
```

### 2. Create and activate a Python virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Python dependencies

```powershell
pip install -r requirements.txt
```

Depending on the current voice features being tested, additional requirement files may exist for STT/TTS components.

### 4. Configure environment

Copy the example environment file if present:

```powershell
copy .env.example .env
```

Then update `.env` for your local setup.

Common settings include:

```env
JARVIS_LLM_PROVIDER=lm_studio
JARVIS_STT_MODEL=medium.en
JARVIS_STT_DEVICE=auto
JARVIS_STT_COMPUTE_TYPE=auto
```

### 5. Install app-shell dependencies

```powershell
cd app_shell
npm install
cd ..
```

### 6. Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

Or use the Windows launcher if present:

```text
Start_Jarvis_Ultimate_App.bat
```

---

## Testing

Run the full unit test suite with:

```powershell
python -m unittest discover -s tests -v
```

Tests are expected to avoid launching real apps during unit testing. App-control behavior should use dry-run/mocked pathways inside tests and real launches only when Jarvis is running normally.

---

## Local data and privacy

Jarvis is designed to store runtime data locally.

Local data may include:

- app discovery cache,
- learned app aliases,
- memory files,
- chat archive files,
- logs,
- temporary voice output,
- runtime diagnostics.

Before making the repository public, sensitive or machine-specific data should stay out of Git. Typical local-only paths include:

```text
.env
data/
logs/
.patch_backups/
app_shell/node_modules/
__pycache__/
*.pyc
```

This project is intended to be public as source code, not as a dump of personal runtime memory, logs, secrets, or local app paths.

---

## Development workflow

Updates are built as patch packages.

Each patch should include:

- an `apply_..._patch.py` installer script,
- a `patch_files/` folder,
- patch notes,
- a testing guide,
- updated handoff instructions,
- no `START_HERE` file,
- no README outside `patch_files/` inside patch packages.

After applying a patch:

```powershell
python -m unittest discover -s tests -v
```

Then clean up temporary patch files before committing:

```powershell
Remove-Item .\apply_<patch_name>.py -Force
Remove-Item .\patch_files -Recurse -Force
```

Then commit:

```powershell
git add .
git commit -m "<version> <summary>"
git push
```

---

## Version history highlights

### 0.1.x — Native interface foundation

- Desktop app-shell foundation
- Voice bridge
- Sleep/wake state handling
- UI polish and orb behavior

### 0.2.x — Core usability foundations

- App Agent expansion
- smart app discovery
- app open/close/focus
- learned app aliases
- default app roles
- voice caption synchronization
- explicit long-term memory
- short-term memory
- daily chat archive foundation

### 0.3.0 — Memory Auto-Capture + Candidate Review

- automatic memory candidate capture,
- memory candidate review queue,
- promotion/rejection workflow,
- automatic short-term context capture,
- LLM-ready memory tier classification behind a safe config flag.

### 0.3.1 — Scalable Entity Memory Foundation

- structured entity memory store,
- registry-driven entity types,
- default entities for user/person/pet/project/app/place/device/vehicle/organization,
- entity search/list/status support through Memory Agent,
- entity memory context injection into LLM conversation,
- entity updates from explicit memories and approved memory candidates,
- SaaS-ready fields for scope, sensitivity, metadata, and future tenant/workspace logic.

### Next: 0.3.2

Planned next milestone:

- entity memory polish,
- memory preference controls,
- high-confidence auto-promotion rules,
- entity edit/merge/delete commands,
- SaaS workspace/team scoping.

---

## Roadmap

Near-term roadmap:

- Entity Memory Polish
- Memory Candidate Review Polish + Auto-Promotion Rules
- File Agent Foundation
- Routine Agent Foundation
- Web/Weather Agent expansion
- richer UI action cards
- resizable/rearrangeable panels

Long-term roadmap:

- screen awareness,
- camera awareness,
- face/person identity memory,
- security-system control,
- routine automation,
- voice-first project development workflows,
- SaaS-ready user/device separation,
- deeper local AI orchestration.

---

## Recruiter / reviewer notes

This project demonstrates practical work across:

- Python application architecture,
- desktop app integration,
- local AI/LLM workflows,
- voice assistant pipelines,
- agent-based design,
- persistent memory systems,
- UI/UX iteration,
- automated testing,
- Windows desktop automation,
- long-running local-service design.

Jarvis Ultimate is not a finished commercial product. It is an active engineering project focused on building a real local AI assistant one tested system at a time.

---

## License

Add your chosen license here before publishing publicly.

