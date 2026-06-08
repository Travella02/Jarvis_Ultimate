# Testing Guide — 0.0.9 STT / Microphone Input Foundation

## 1. Apply the patch

From the patch zip, copy these into the Jarvis Ultimate root:

```text
apply_0_0_9_stt_microphone_foundation_patch.py
patch_files/
```

Then run:

```powershell
python apply_0_0_9_stt_microphone_foundation_patch.py
```

## 2. Install STT dependencies

From the Jarvis Ultimate root with `.venv` active:

```powershell
python -m pip install -r requirements-stt.txt
```

This installs microphone recording support and the local/offline faster-whisper STT provider.

If you skip this step, Jarvis should still boot, but `stt status` will report that the real STT dependencies are unavailable and that mock fallback is ready.

## 3. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Expected:

```text
Ran 102 tests
OK
```

## 4. Boot check

```powershell
python scripts/run_jarvis.py
```

Expected:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 5. CLI STT checks

Start the CLI:

```powershell
python scripts/run_cli.py
```

Run:

```text
stt status
stt providers
```

Expected after installing `requirements-stt.txt`:

```text
preferred provider: faster_whisper
fallback providers: mock
microphone: ready
faster_whisper: ready
```

If dependencies are not installed yet, expected safe fallback state:

```text
faster_whisper: unavailable
mock: ready
```

## 6. Microphone recording test

Run:

```text
stt record
```

Expected:

```text
Microphone recording saved.
Output: ...data\stt\jarvis_mic_....wav
```

If this fails, common meanings:

- `sounddevice` missing: run `python -m pip install -r requirements-stt.txt`
- no input device: Windows microphone permissions/device selection issue
- invalid device: clear `JARVIS_STT_MICROPHONE_DEVICE=` or choose the right device later

## 7. One-shot listen test

Run:

```text
listen once
```

Speak a short phrase during the recording window, for example:

```text
hello jarvis this is a microphone test
```

Expected:

```text
faster-whisper transcription complete.
Heard: ...
Provider: faster_whisper
```

Then run:

```text
stt debug last
```

Expected:

```text
Last STT debug:
- final success: True
- final provider: faster_whisper
```

## 8. Audio-file transcription test

Use the WAV path created by `stt record`:

```text
stt transcribe C:\path\to\jarvis_mic_....wav
```

Expected:

```text
Heard: ...
Provider: faster_whisper
```

## 9. Do not commit until this passes

Only commit after:

- full tests pass
- Jarvis boots
- `stt status` works
- `stt providers` works
- `stt record` either records successfully or gives a clear dependency/device error
- `listen once` transcribes successfully, or you have captured the dependency/device error for the next fix

## 10. Cleanup before commit

After successful testing, remove the temporary installer files:

```powershell
Remove-Item apply_0_0_9_stt_microphone_foundation_patch.py
Remove-Item -Recurse patch_files
```

Then commit:

```powershell
git add .
git commit -m "0.0.9 Add STT microphone input foundation"
git push
```
