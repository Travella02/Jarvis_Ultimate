# Testing Guide — 0.1.4 Sleep/Wake Always-Listening Conversation Mode

Run all commands from the Jarvis Ultimate project root with the virtual environment active.

## 1. Install the patch

```powershell
python apply_0_1_4_sleep_wake_always_listening_patch.py
```

## 2. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 151 tests
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

## 4. Manual CLI check

```powershell
python scripts/run_cli.py
```

Then run:

```text
wake status
sleep wake status
warmup all
sleep wake start max 6 timeout 20
```

## 5. Manual speech flow

Say a non-wake sentence first, such as:

```text
I am talking to someone else.
```

Expected: Jarvis should ignore it and stay asleep.

Then say:

```text
Hey Jarvis, give me one short sentence.
```

Expected: Jarvis detects the wake phrase, routes only `give me one short sentence`, answers, and speaks.

Then say a follow-up without the wake word:

```text
Make it even shorter.
```

Expected: Jarvis should respond because he is awake.

Then say:

```text
That's all Jarvis.
```

Expected: Jarvis returns to sleep mode.

Then say another non-wake sentence:

```text
I am talking to someone else again.
```

Expected: Jarvis ignores it because he is asleep again.

To stop the CLI loop fully, say:

```text
Exit voice mode.
```

Or press `Ctrl+C`.

## 6. Inactivity timeout test

Run:

```text
sleep wake start max 10 timeout 10
```

Say:

```text
Hey Jarvis.
```

Then do not speak. After the timeout passes, Jarvis should report that he returned to sleep mode.

## 7. Cleanup and commit

Only after tests and manual checks pass:

```powershell
Remove-Item apply_0_1_4_sleep_wake_always_listening_patch.py
Remove-Item -Recurse patch_files

git add .
git commit -m "0.1.4 Add sleep/wake always-listening voice mode"
git push
```
