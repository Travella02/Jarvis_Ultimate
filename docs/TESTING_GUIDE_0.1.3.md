# Testing Guide — 0.1.3 Continuous Hands-Free Voice Loop

Run all commands from the Jarvis Ultimate root with the venv active.

## 1. Run tests

```powershell
python -m unittest discover -s tests -v
```

Expected:

```text
Ran 147 tests
OK
```

## 2. Boot check

```powershell
python scripts/run_jarvis.py
```

Expected:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 3. CLI check

```powershell
python scripts/run_cli.py
```

Run:

```text
voice loop status
handsfree status
stt listen settings
warmup all
```

Expected:

- Status mentions continuous mode.
- STT/TTS warmup works or reports clearly why a provider is unavailable.

## 4. Wake-required continuous loop test

Run:

```text
handsfree start max 3
```

Speak one command with the wake word:

```text
Hey Jarvis, give me one short sentence.
```

Then stop it:

```text
Hey Jarvis, stop listening.
```

Success looks like:

- Jarvis prints `Heard: ...`
- Jarvis detects the wake command.
- Jarvis streams and speaks the response.
- Jarvis stops after the spoken stop phrase.

## 5. Faster endpointing test

Run:

```text
wake loop start max 3 silence 0.55
```

If Jarvis cuts you off, use:

```text
wake loop start max 3 silence 0.8
```

## 6. No-wake controlled conversation test

Only use this in a quiet room:

```text
conversation start max 3
```

Speak normal turns without saying `Hey Jarvis`.

Success looks like:

- Jarvis handles each turn directly.
- Saying `stop listening` exits the loop.

## 7. Cleanup

If tests and manual checks pass, remove installer files:

```powershell
Remove-Item apply_0_1_3_continuous_handsfree_voice_loop_patch.py
Remove-Item -Recurse patch_files
```

Then commit:

```powershell
git add .
git commit -m "0.1.3 Add continuous hands-free voice loop"
git push
```
