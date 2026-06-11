# Jarvis Ultimate 0.1.9a Testing Guide

## 1. Run the automated tests

From the Jarvis Ultimate project root, run:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

This patch was validated with 209 passing tests.

## 2. Start the native app shell

```powershell
python scripts\start_jarvis_app.py
```

Expected result:

- The Electron app opens.
- Voice warmup runs.
- Auto Wake starts sleep/wake mode after warmup.
- The orb enters a dimmer, slower sleep-mode visual while waiting for the wake phrase.

## 3. Check panel layout

Verify:

- Runtime, Voice, Workspace, and Conversation panels do not overlap.
- The left rail scrolls safely if the window is too short.
- The bottom diagnostics drawer does not cover the voice controls.

## 4. Check panel controls

Use the top bar buttons:

- Runtime
- Voice
- Workspace
- Chat
- Diagnostics
- Orb Only

Expected result:

- Each panel can be hidden and shown again.
- Hide buttons inside panels also hide that specific panel.
- Orb Only hides the side panels and diagnostics so Jarvis can be viewed as a clean main orb.
- Panel choices persist after refresh/relaunch because they are saved in local storage.

## 5. Check Jarvis states

Test these states:

- Sleep/wake waiting: dim grey-blue and slow animation.
- Listening: brighter cyan-blue.
- Thinking: purple.
- Speaking: deeper blue with voice waves.
- Error: red alert style.

## 6. Check voice startup

With Auto Wake on:

1. Launch the app.
2. Wait for warmup to say ready.
3. Confirm sleep/wake starts without clicking Start Sleep/Wake.
4. Say a wake phrase and ask Jarvis a question.
5. Say a sleep phrase or press Stop Voice.

Expected result:

- Jarvis starts in sleep/wake mode automatically.
- Pressing Stop Voice stops the current voice session and does not immediately restart it.
