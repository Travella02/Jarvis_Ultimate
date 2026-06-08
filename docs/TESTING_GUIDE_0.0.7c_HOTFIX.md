# Testing Guide — 0.0.7c Kokoro Test Hotfix

## Purpose

This hotfix fixes a test-only issue where the mock fallback test failed on machines with Kokoro installed. It does not change runtime TTS behavior.

## Apply the hotfix

From the Jarvis Ultimate project root:

```powershell
python apply_0_0_7c_kokoro_test_hotfix_patch.py
```

## Required automated test

Run:

```powershell
python -m unittest discover -s tests -v
```

Success should end with:

```text
Ran 86 tests
OK
```

## Manual Kokoro check

Start the CLI:

```powershell
python scripts/run_cli.py
```

Then run:

```text
tts status
tts providers
tts voice list
tts voice use af_bella
tts voice current
tts voice test af_bella play
tts test play
```

Success should show Kokoro as the preferred provider and mock as the fallback. Playback should work if your Windows audio output is available.

## Cleanup before commit

After tests and manual checks pass, remove the temporary installer files:

```powershell
Remove-Item apply_0_0_7c_kokoro_test_hotfix_patch.py
Remove-Item -Recurse patch_files
```

Then commit 0.0.7c:

```powershell
git add .
git commit -m "0.0.7c Make Kokoro the default TTS provider"
git push
```
