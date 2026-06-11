# Jarvis Ultimate 0.1.8a Testing Guide

## Goal
Verify that the native app shell keeps the voice controls visible, keeps the orb in speaking mode through playback, and warms the voice systems before conversation.

## 1. Run the automated tests
From the main project folder:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## 2. Launch the native app shell
From the main project folder:

```powershell
python scripts\start_jarvis_app.py
```

Expected result:
- The Electron Jarvis Ultimate app opens.
- The bridge status says online.
- The voice status card includes a Warmup field.
- The voice controls are visible below the orb.

## 3. Test voice warmup readiness
When the app opens, check the voice status card.

Expected result:
- Warmup should show `ready` after the Python bridge finishes warming systems.
- Listen Once and Start Sleep/Wake should be usable only after warmup is ready.

If the app takes longer to open, that can be normal because the bridge may be loading STT/TTS models before showing itself as ready.

## 4. Test Listen Once speaking state
In the app:

1. Click `Listen Once`.
2. Say: `Hey Jarvis, what's your status?`
3. Watch the orb while Jarvis answers.

Expected result:
- The orb changes to listening while recording.
- The orb changes to thinking while Jarvis routes the command.
- The orb changes to speaking and should stay speaking until the audible response finishes.
- After speech finishes, the orb can return to idle.

## 5. Test button layout
After a Listen Once turn finishes, confirm:

- `Listen Once` is visible.
- `Start Sleep/Wake` is visible.
- `Stop Voice` is visible when a voice session is running.
- None of the voice controls are hidden underneath the Conversation panel.

If the window is very short, the center orb panel should scroll internally instead of letting buttons disappear behind the bottom panel.

## 6. Test Sleep/Wake
In the app:

1. Click `Start Sleep/Wake`.
2. Say: `Hey Jarvis, what's your status?`
3. Let Jarvis respond.
4. Click `Stop Voice`.

Expected result:
- Sleep/Wake mode should listen for a wake phrase.
- The orb should show speaking during playback.
- Stop Voice should request a clean stop.

## 7. Cleanup before commit
After the patch is working, remove the temporary patch installer and patch folder:

```powershell
Remove-Item .\apply_0_1_8a_app_shell_voice_readiness_patch.py -Force
Remove-Item .\patch_files -Recurse -Force
```

Do not delete `app_shell/`.
