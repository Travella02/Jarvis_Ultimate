# Testing Guide — 0.1.0 Real Voice Loop

Run all commands from the Jarvis Ultimate project root with the virtual environment active.

## 1. Apply the patch

```powershell
python apply_0_1_0_real_voice_loop_patch.py
```

## 2. Run automated tests

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 118 tests
OK
```

The exact runtime may vary.

## 3. Boot check

```powershell
python scripts/run_jarvis.py
```

Expected:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 4. Manual CLI checks

```powershell
python scripts/run_cli.py
```

Run:

```text
voice loop status
stt warmup
voice loop once
```

Speak a short command, for example:

```text
Hey Jarvis, say one short sentence.
```

Expected behavior:

1. Jarvis listens with smart endpointing.
2. Jarvis prints what he heard.
3. Jarvis streams a response in the CLI.
4. Jarvis speaks the response through TTS.

## 5. Latency tuning checks

Try:

```text
voice loop smart max 8 silence 0.8
voice loop smart max 8 silence 1.2
voice loop fixed 2
```

Expected:

- `silence 0.8` should stop faster.
- `silence 1.2` should feel safer but slightly slower.
- `fixed 2` should record for exactly about two seconds.

## 6. Debug commands

If the voice loop does not work, run:

```text
stt debug last
tts queue status
tts debug last
timing last
```

## 7. Commit guidance

Do not commit until:

- tests pass,
- `voice loop status` works,
- `voice loop once` transcribes correctly,
- Jarvis streams a response,
- Jarvis speaks the response.

Then clean up installer files:

```powershell
Remove-Item apply_0_1_0_real_voice_loop_patch.py
Remove-Item -Recurse patch_files
```

Commit:

```powershell
git add .
git commit -m "0.1.0 Add real voice loop"
git push
```
