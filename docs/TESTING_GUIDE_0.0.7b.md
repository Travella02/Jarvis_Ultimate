# Testing Guide — 0.0.7b XTTS Multi-Voice Profiles + TTS Debugging

Run all commands from the Jarvis Ultimate project root with the virtual environment active.

## 1. Apply the patch

Copy these into the project root:

```text
apply_0_0_7b_xtts_multi_voice_debug_patch.py
patch_files/
```

Run:

```powershell
python apply_0_0_7b_xtts_multi_voice_debug_patch.py
```

## 2. Run automated tests

```powershell
python -m unittest discover -s tests -v
```

Success should look like:

```text
Ran 83 tests
OK
```

## 3. Boot check

```powershell
python scripts/run_jarvis.py
```

Success should look like:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 4. CLI checks

```powershell
python scripts/run_cli.py
```

Run:

```text
tts status
tts voice list
tts voice current
tts debug last
```

Expected:

- `tts status` shows the current voice and voice profiles directory.
- `tts voice list` shows imported voice profiles, or says none are imported yet.
- `tts debug last` says no TTS request has run yet if you have not generated voice in this session.

## 5. Import a voice profile

Use a clean WAV reference. Recommended:

- 10–30 seconds
- one person speaking
- mono if possible
- little or no background noise
- WAV format

Example:

```text
tts voice import jarvis C:\Users\tanne\Desktop\jarvis_reference.wav
```

Then run:

```text
tts voice list
tts voice current
```

Success should show `jarvis` as the current voice and should show a copied reference path under:

```text
data\tts\voices\jarvis\reference.wav
```

Warnings about short/stereo audio do not always mean failure; they mean XTTS may clone less reliably.

## 6. Test XTTS directly without fallback

Run:

```text
tts xtts test play
```

or:

```text
tts voice test jarvis play
```

If XTTS works, success should show:

```text
Provider: xtts
Played: True
```

If XTTS fails, this is now useful. Immediately run:

```text
tts debug last
```

Send the debug output back for diagnosis. It should show the exact XTTS exception instead of silently falling back to Kokoro.

## 7. Test fallback behavior

Run:

```text
tts test play
```

This uses the normal provider chain. If XTTS fails, Jarvis may fall back to Kokoro or mock. That is expected for normal reliability. Run `tts debug last` to see why fallback happened.

## 8. Test multiple voices

Import another voice only if you have permission to use that person’s voice:

```text
tts voice import me C:\Users\tanne\Desktop\me_reference.wav
tts voice list
tts voice use me
tts voice test me play
tts say as jarvis Hello sir, this is the Jarvis profile.
tts say as me Hello sir, this is the me profile.
```

## 9. Test persona change

With LM Studio running, send a normal chat message:

```text
hey jarvis
```

Jarvis should be encouraged by the system prompt to address you as “sir” instead of “Tanner.”

## 10. Cleanup after successful testing

After tests and manual checks pass, remove temporary installer files:

```powershell
Remove-Item apply_0_0_7b_xtts_multi_voice_debug_patch.py
Remove-Item -Recurse patch_files
```

Then commit:

```powershell
git add .
git commit -m "0.0.7b Add XTTS multi-voice profiles and TTS debugging"
git push
```

Do not commit until the automated tests and manual checks pass.
