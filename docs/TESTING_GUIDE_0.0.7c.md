# Testing Guide — 0.0.7c Kokoro Default TTS Cleanup

Run these from the Jarvis Ultimate root with the virtual environment active.

## 1. Install the patch

```powershell
python apply_0_0_7c_kokoro_default_tts_cleanup_patch.py
```

The installer also tries to update your project-root `.env` so the active TTS provider becomes Kokoro:

```env
JARVIS_TTS_PROVIDER=kokoro
JARVIS_TTS_FALLBACK_PROVIDERS=mock
JARVIS_TTS_USE_GPU=false
JARVIS_TTS_DEVICE=auto
```

## 2. Install Kokoro TTS requirements

On a machine that does not already have Kokoro installed, run:

```powershell
python -m pip install -r requirements-tts.txt
```

This is the main/default TTS requirements file after 0.0.7c. It does not install XTTS.

## 3. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 86 tests
OK
```

The exact test count may increase later, but it should finish with `OK`.

## 4. Boot check

```powershell
python scripts/run_jarvis.py
```

Expected result:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 5. CLI voice checks

```powershell
python scripts/run_cli.py
```

Run:

```text
tts status
tts providers
tts voice list
tts voice current
```

Success should show:

```text
preferred provider: kokoro
fallback providers: mock
Kokoro voice: af_heart
```

## 6. Kokoro voice switch check

Run:

```text
tts voice use af_bella
tts voice current
tts voice test af_bella play
```

Success should show the current Kokoro voice as `af_bella`. If optional Kokoro dependencies are installed, `tts voice test af_bella play` should generate speech and attempt playback.

## 7. Normal TTS playback check

Run:

```text
tts test play
tts say Hello sir. This is Jarvis using Kokoro.
```

Expected:

- Provider should be `kokoro` when Kokoro dependencies are installed.
- If Kokoro is missing, Jarvis should fall back safely to `mock` instead of crashing.
- Jarvis should not try XTTS unless you explicitly select/test XTTS.

## 8. Commit only after checks pass

After tests and manual checks pass, remove the installer files:

```powershell
Remove-Item apply_0_0_7c_kokoro_default_tts_cleanup_patch.py
Remove-Item -Recurse patch_files
```

Then commit:

```powershell
git add .
git commit -m "0.0.7c Make Kokoro the default TTS provider"
git push
```
