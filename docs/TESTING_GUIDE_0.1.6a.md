# Testing Guide — 0.1.6a Desktop Full Runtime Launcher

## Goal

Confirm the desktop UI is connected to the real Jarvis voice runtime and that Jarvis can be started from one launcher instead of manually starting separate pieces.

## Install

From the Jarvis Ultimate project root, copy in the patch installer and `patch_files/`, then run:

```powershell
python apply_0_1_6a_desktop_full_runtime_launcher_patch.py
```

## Required automated tests

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected:

```text
Ran 167 tests
OK
```

## Boot checks

Run:

```powershell
python scripts/run_jarvis.py
```

Expected:

```text
Jarvis 3 is online. Registered 9 agents.
```

Then run the desktop:

```powershell
python scripts/start_jarvis.py
```

or:

```powershell
python scripts/run_desktop.py
```

On Windows you can also double-click:

```text
Start_Jarvis_Ultimate.bat
```

## Manual desktop checks

1. Confirm the Jarvis Ultimate desktop window opens.
2. Confirm the left status panel shows the desktop voice runtime status.
3. Confirm the avatar/orb area shows a voice state.
4. If auto-start voice is enabled, Jarvis should automatically enter sleep/wake voice mode after boot/warmup.
5. Say non-wake speech such as:

```text
I am talking to someone else.
```

Expected: Jarvis should ignore it while asleep.

6. Say:

```text
Hey Jarvis, give me one short sentence.
```

Expected:

- The chat panel should show what Jarvis heard.
- Jarvis should stream/respond in the chat panel.
- Jarvis should speak through TTS.
- The avatar/status should update through listening/thinking/speaking states.

7. Say a follow-up without wake word while Jarvis is awake:

```text
Make it even shorter.
```

Expected: Jarvis should answer because he is awake.

8. Say:

```text
That's all Jarvis.
```

Expected: Jarvis should return to sleep mode.

9. Click **Stop Voice**.

Expected: Jarvis should request voice runtime shutdown. It may stop after the current listen turn completes.

10. Click **Start Voice**.

Expected: Jarvis should restart the sleep/wake voice runtime from the UI.

11. Click **Warm Up**.

Expected: Jarvis should warm configured STT/TTS systems without freezing the UI.

## Troubleshooting

### Desktop opens but voice does not auto-start

Check `.env`:

```env
JARVIS_DESKTOP_AUTO_START_VOICE=true
JARVIS_VOICE_ALWAYS_LISTENING_ON_STARTUP=true
JARVIS_VOICE_ALWAYS_LISTENING_MAX_TURNS=0
```

Then restart the desktop.

### Stop Voice does not stop instantly

That is expected for now. The current STT listen turn must finish first. This is safer than killing the microphone thread. Barge-in/instant interrupt can be added later.

### Jarvis hears himself

This can still happen depending on speaker/mic setup. The current loop waits for TTS to become idle before listening again, but echo cancellation/barge-in is a later improvement.

## Commit only after

- tests pass
- desktop opens
- Jarvis can start voice from the UI
- Jarvis can stop voice from the UI
- the one-file startup launcher works
