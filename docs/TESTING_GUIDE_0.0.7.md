# Testing Guide — 0.0.7 TTS Provider Foundation

## 1. Install the patch

From the Jarvis Ultimate root:

```powershell
python apply_0_0_7_tts_provider_foundation_patch.py
```

## 2. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Success should show all tests passing. The expected clean patch result is:

```text
Ran 70 tests
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

## 4. CLI TTS checks

```powershell
python scripts/run_cli.py
```

Then run:

```text
tts status
tts providers
tts test
tts say Hello Tanner. This is a Jarvis voice test.
```

On a fresh install without XTTS/Kokoro dependencies, success can still fall back
to the mock provider. That is okay for this foundation patch. You should see an
output path under `data/tts/`, usually as a `.txt` mock placeholder unless real
TTS dependencies are installed.

## 5. Optional real XTTS check

Only do this when you are ready to test GPU TTS:

```powershell
pip install -r requirements-tts.txt
```

Then place a clean reference WAV here:

```text
assets/voices/jarvis_reference.wav
```

Run:

```text
tts status
tts test
```

Success should show XTTS as ready and generate a `.wav` in `data/tts/`.

## 6. Auto voice runtime check

In the CLI:

```text
voice on
hey jarvis
voice off
```

`voice on` only changes the current runtime session. It does not edit `.env`.

## 7. Clean up installer files after success

```powershell
Remove-Item apply_0_0_7_tts_provider_foundation_patch.py
Remove-Item -Recurse patch_files
```

## 8. Commit only after tests and manual checks pass

```powershell
git add .
git commit -m "0.0.7 Add swappable TTS provider foundation"
git push
```
