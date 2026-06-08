# Jarvis Ultimate 0.0.7a Testing Guide — TTS Playback + XTTS Reference Setup

This patch builds on 0.0.7. It does not force voice playback on globally. It adds commands so you can test playback and configure an XTTS speaker reference cleanly.

## 1. Apply the patch

From the Jarvis Ultimate project root:

```powershell
python apply_0_0_7a_tts_playback_xtts_reference_patch.py
```

## 2. Run the automated tests

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 78 tests
OK
```

The exact runtime can vary depending on optional TTS packages installed in your venv.

## 3. Boot check

```powershell
python scripts/run_jarvis.py
```

Expected result:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 4. Manual CLI checks

Start the CLI:

```powershell
python scripts/run_cli.py
```

Run:

```text
tts status
tts providers
tts reference
tts test
tts play last
tts test play
```

Expected behavior:

- `tts status` shows playback support and the XTTS reference path.
- `tts reference` shows whether `assets/voices/jarvis_reference.wav` exists.
- `tts test` generates a WAV file without forcing playback.
- `tts play last` tries to play the most recently generated WAV.
- `tts test play` generates a test WAV and tries to play it immediately.

If playback fails but the WAV file is generated, the provider foundation is still working. Playback depends on your OS audio setup and whether the generated file is a real WAV. Kokoro/XTTS should produce real WAV files; mock creates a placeholder file for tests.

## 5. XTTS speaker reference setup

Place or import a clean voice reference WAV. Example:

```text
tts reference import C:\Users\tanne\Desktop\jarvis_reference.wav
```

Then run:

```text
tts reference
tts status
tts test play
```

Success looks like:

```text
XTTS reference ready: True
```

If XTTS is installed and the speaker reference is ready, Jarvis should use XTTS. If XTTS fails, Jarvis should fall back to Kokoro or mock.

## 6. Voice auto-speak check

In the CLI:

```text
voice on
hey jarvis
voice off
```

Expected behavior:

- `voice on` enables auto-speak and playback for this runtime session.
- A normal successful Jarvis chat response should generate speech and try to play it.
- `voice off` turns auto-speak and playback off again.

## 7. Cleanup before commit

After tests and manual checks pass:

```powershell
Remove-Item apply_0_0_7a_tts_playback_xtts_reference_patch.py
Remove-Item -Recurse patch_files
```

Then commit:

```powershell
git add .
git commit -m "0.0.7a Add TTS playback and XTTS reference setup"
git push
```

Do not commit if automated tests fail or if the CLI commands are missing.
