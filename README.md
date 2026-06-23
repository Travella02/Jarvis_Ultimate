# Jarvis Ultimate

Jarvis Ultimate is a local-first desktop AI assistant project with a Python runtime, Electron app shell, local LLM integration, voice input/output, modular agents, and an expanding always-on memory system.

## Current milestone

Current version: **0.3.6 — Sensitive Chat Redaction + Memory Log Hygiene**

This version keeps normal memory useful while preventing sensitive values from leaking into local chat archives, memory candidate metadata, UI chat history, and JSONL logs. Passwords, API keys, account numbers, recovery codes, and similar values are routed away from normal memory toward the future Secure Vault / Password Manager Agent path.

## Core capabilities

- Local-first Jarvis runtime
- Electron native app shell
- LM Studio-compatible local LLM provider
- Faster Whisper STT
- Kokoro TTS
- Sleep/wake voice loop
- Typed input voice parity
- App Agent with launch/close/focus/alias support
- Long-term memory
- Short-term fact memory
- Chat archive memory
- Memory candidate review
- Scalable entity memory
- Entity aliases, merges, and phonetic name recovery
- Relationship memory graph
- Memory preferences and auto-remember controls
- Sensitive memory secure-vault routing foundation
- Sensitive chat/log redaction hygiene

## Testing

Run:

```powershell
python -m unittest discover -s tests -v
```

## Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

Or double-click:

```powershell
Start_Jarvis_Ultimate_App.bat
```

## Privacy and memory notes

Jarvis stores memory locally by default. Normal memory should be used for user preferences, projects, people, pets, apps, settings, relationships, and daily context. Sensitive values should not be saved in normal memory. The 0.3.6 redaction layer masks sensitive values before they are written into chat archives, UI history state, memory candidate metadata, and JSONL logs.

Full encrypted Secure Vault / Password Manager Agent storage is not implemented yet. Until that dedicated feature exists, Jarvis routes sensitive save requests away from normal memory and explains that encrypted local vault storage is not enabled.
