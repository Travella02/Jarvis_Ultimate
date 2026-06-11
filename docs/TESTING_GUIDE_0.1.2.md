# Testing Guide — 0.1.2 Always-Ready Voice Runtime Cleanup

Run all commands from the Jarvis Ultimate project root with the virtual environment active.

## 1. Apply the patch

```powershell
python apply_0_1_2_always_ready_voice_runtime_patch.py
```

## 2. Run the automated tests

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 137 tests
OK
```

## 3. Boot check

```powershell
python scripts/run_jarvis.py
```

Expected result:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 4. CLI checks

```powershell
python scripts/run_cli.py
```

Run:

```text
stt listen settings
warmup status
warmup all
tts status
stt status
```

Expected:

- `stt listen settings` shows silence stop around `0.75` seconds unless your `.env` overrides it.
- `warmup all` warms STT and TTS or reports a clear provider issue.
- `tts status` shows retention for generated WAV files.
- `stt status` shows retention for microphone WAV files.

## 5. Responsiveness tuning checks

Run:

```text
listen faster
stt listen settings
listen once
listen balanced
listen safer
stt silence 0.8
stt listen settings
```

Success means Jarvis updates the runtime silence value and `listen once` still transcribes correctly.

Suggested settings:

- `listen faster` for fastest handoff, but it may cut you off.
- `listen balanced` for normal conversation.
- `listen safer` if Jarvis stops listening too early.
- `stt silence 0.8` for custom tuning.

## 6. Cleanup checks

Run:

```text
audio cleanup
tts cleanup
stt cleanup
```

Success means Jarvis reports how many old files were removed. Removing `0` files is fine if you have not generated enough audio files yet.

## 7. Voice loop check

Run:

```text
wake voice once
```

Say:

```text
Hey Jarvis, give me one short sentence.
```

Success means Jarvis hears you, strips the wake phrase, responds, and speaks the answer.

## Commit guidance

Only commit after:

- tests pass,
- `warmup all` behaves correctly,
- `listen once` or `wake voice once` still works,
- cleanup commands do not error.

Then clean up patch files:

```powershell
Remove-Item apply_0_1_2_always_ready_voice_runtime_patch.py
Remove-Item -Recurse patch_files
```

Commit:

```powershell
git add .
git commit -m "0.1.2 Add always-ready voice runtime cleanup"
git push
```
