# Testing Guide — 0.1.5a Sleep Phrase Robustness Hotfix

Run all commands from the Jarvis Ultimate project root with the virtual environment active.

## 1. Apply the patch
```powershell
python apply_0_1_5a_sleep_phrase_robustness_hotfix_patch.py
```

## 2. Run the full test suite
```powershell
python -m unittest discover -s tests -v
```

Expected result:
```text
Ran 157 tests
OK
```

The exact runtime may vary. The important part is `OK`.

## 3. Boot check
```powershell
python scripts/run_jarvis.py
```

Expected result:
```text
Jarvis 3 is online. Registered 9 agents.
```

## 4. Manual sleep/wake check
Run:
```powershell
python scripts/run_cli.py
```

If always-listening is enabled, Jarvis should automatically enter sleep mode. If not, run:
```text
sleep wake start max 8 timeout 20
```

Test this flow:

1. Say something that does not include a wake phrase, such as:
   ```text
   I am talking to someone else.
   ```
   Expected: Jarvis ignores it while asleep.

2. Say:
   ```text
   Hey Jarvis, give me one short sentence.
   ```
   Expected: Jarvis wakes, routes the command, and speaks/responds.

3. Say a follow-up without the wake word:
   ```text
   Make it shorter.
   ```
   Expected: Jarvis responds because he is awake.

4. Say:
   ```text
   That's all Jarvis.
   ```
   Expected: Jarvis returns to sleep mode.

5. If STT mishears it as `That's all Dervis`, `That's all Jervis`, or similar, Jarvis should still return to sleep.

6. Stop the loop by saying:
   ```text
   Exit voice mode.
   ```
   or press `Ctrl+C`.

## 5. Commit only after success
If tests pass and Jarvis returns to sleep after the sleep phrase, remove installer files:
```powershell
Remove-Item apply_0_1_5a_sleep_phrase_robustness_hotfix_patch.py
Remove-Item -Recurse patch_files
```

Then commit:
```powershell
git add .
git commit -m "0.1.5a Improve sleep phrase robustness"
git push
```
