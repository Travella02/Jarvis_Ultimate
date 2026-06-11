# Testing Guide — 0.1.1 Wake Word Foundation

Run these commands from the Jarvis Ultimate root with the virtual environment active.

## 1. Install the patch

```powershell
python apply_0_1_1_wake_word_foundation_patch.py
```

## 2. Run automated tests

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 132 tests
OK
```

The exact run time may differ.

## 3. Boot check

```powershell
python scripts/run_jarvis.py
```

Success looks like:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 4. CLI wake-word checks

```powershell
python scripts/run_cli.py
```

Then run:

```text
wake status
wake test Hey Jarvis, give me one sentence
wake test This should not wake you
```

Success looks like:

```text
Detected: True
Wake word: hey jarvis
Command after wake word: give me one sentence
```

For the second command, success is:

```text
Detected: False
```

## 5. Microphone wake-listen test

Run:

```text
wake listen once
```

Say:

```text
Hey Jarvis, status
```

Success looks like:

```text
Heard: Hey Jarvis, status
Detected: True
Command after wake word: status
```

## 6. One-turn wake voice test

Run:

```text
wake voice once
```

Say:

```text
Hey Jarvis, give me one short sentence.
```

Success looks like:

1. Jarvis hears your transcript.
2. Jarvis detects the wake word.
3. Jarvis sends the command after the wake word to the brain.
4. Jarvis streams a response.
5. Jarvis speaks the response with Kokoro.

## 7. Empty wake test

Run:

```text
wake voice once
```

Say only:

```text
Hey Jarvis
```

Success looks like:

```text
Yes, sir?
```

## 8. Tuning

The wake listener uses the same smart STT endpointing settings as `listen once`.

Try:

```text
wake loop smart max 8 silence 0.8
wake loop smart max 8 silence 1.2
```

Lower silence values feel faster but can cut you off. Higher values are safer but slower.

## 9. Cleanup after success

After tests and manual checks pass:

```powershell
Remove-Item apply_0_1_1_wake_word_foundation_patch.py
Remove-Item -Recurse patch_files
```

Then commit:

```powershell
git add .
git commit -m "0.1.1 Add wake word foundation"
git push
```

Do not commit until the tests and manual wake-word checks pass.
