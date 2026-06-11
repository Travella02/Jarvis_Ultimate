# Testing Guide — 0.1.5 Always-On Startup Voice Mode

Run these from the Jarvis Ultimate project root with the virtual environment active.

## 1. Install the patch

```powershell
python apply_0_1_5_always_on_startup_voice_mode_patch.py
```

## 2. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 155 tests
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

If voice warmup is enabled in `.env`, this command may take longer while STT/TTS warm.

## 4. Manual CLI status check without committing yet

Start the normal CLI:

```powershell
python scripts/run_cli.py
```

Because 0.1.5 enables always-listening startup in `.env`, Jarvis should automatically enter sleep/wake mode after boot. You should see text similar to:

```text
Startup always-listening is enabled.
Jarvis is now in sleep mode, waiting for a wake phrase.
Listening turn 1/∞ (sleeping)...
```

## 5. Sleep/wake manual check

While Jarvis is sleeping, say something that does **not** include a wake phrase, such as:

```text
I am talking to someone else.
```

Expected: Jarvis ignores it and stays asleep.

Then say:

```text
Hey Jarvis, give me one short sentence.
```

Expected:

- Jarvis detects the wake phrase.
- Jarvis wakes up.
- Jarvis routes only the command after the wake phrase.
- Jarvis answers and speaks.

Then say a follow-up without the wake word:

```text
Make it even shorter.
```

Expected: Jarvis answers because he is awake.

Then say:

```text
That's all Jarvis.
```

Expected: Jarvis returns to sleep mode.

To stop the process completely, say:

```text
Exit voice mode.
```

or press `Ctrl+C`.

## 6. Optional dedicated voice launcher

You can also test:

```powershell
python scripts/run_jarvis_voice.py
```

Expected: same startup always-listening behavior.

## 7. Cleanup after successful tests

```powershell
Remove-Item apply_0_1_5_always_on_startup_voice_mode_patch.py
Remove-Item -Recurse patch_files
```

## 8. Commit only after tests and manual checks pass

```powershell
git add .
git commit -m "0.1.5 Add always-on startup voice mode"
git push
```
