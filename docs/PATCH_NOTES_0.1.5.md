# Jarvis Ultimate 0.1.5 — Always-On Startup Voice Mode

## Summary

0.1.5 makes the sleep/wake voice loop usable as Jarvis's normal runtime mode instead of a manually started max-turn test loop.

Jarvis can now:

1. boot,
2. warm voice systems automatically,
3. enter sleep mode,
4. wait for wake phrases such as `hey jarvis`, `jarvis`, or `yo jarvis`,
5. hold a continuous conversation while awake,
6. return to sleep when told phrases such as `that's all Jarvis`, and
7. keep running without a fixed max-turn limit.

## Why this patch exists

The earlier 0.1.4 sleep/wake loop worked, but it still had to be started manually with a command such as:

```text
sleep wake start max 6 timeout 20
```

That made it feel like a test mode, not Jarvis's real always-running state. The goal of 0.1.5 is to make this the normal voice runtime while preserving safe manual CLI tools.

## New behavior

### Startup always-listening mode

The patch adds these settings:

```env
JARVIS_VOICE_ALWAYS_LISTENING_ON_STARTUP=true
JARVIS_VOICE_ALWAYS_LISTENING_MAX_TURNS=0
JARVIS_VOICE_ALWAYS_LISTENING_START_MODE=sleep_wake
```

`0` max turns means no fixed turn limit. Jarvis stays running until you say an exit phrase or press `Ctrl+C`.

### Automatic warmup

The patch also enables voice warmup on boot in `.env`:

```env
JARVIS_VOICE_WARMUP_ON_BOOT=true
JARVIS_VOICE_WARMUP_STT=true
JARVIS_VOICE_WARMUP_TTS=true
JARVIS_VOICE_WARMUP_LLM=false
```

LLM warmup is still off by default because LM Studio may not always be running when Jarvis starts.

### Dedicated voice launcher

A new script is included:

```powershell
python scripts/run_jarvis_voice.py
```

It uses the same runtime as the CLI, but is intended as the dedicated always-listening launcher.

### Infinite sleep/wake loop support

The sleep/wake loop now supports:

```text
sleep wake start forever
sleep wake start max 0
always listening start max 0
```

## Updated commands

```text
startup voice status
always listening startup status
sleep wake start forever
sleep wake start max 0 timeout 45
```

## Notes

This is still a blocking CLI voice runtime, not yet a detached background Windows service. For now, keep the terminal open while Jarvis is running. A later patch can add a tray app, service wrapper, or desktop UI runtime.
