# Testing Guide — 0.1.6c Central Orb Layout + UI State Engine

## 1. Run the full test suite

From the Jarvis Ultimate root with the venv active:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 177 tests
OK
```

The exact time may differ.

## 2. Boot check

```powershell
python scripts/run_jarvis.py
```

Expected:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 3. Desktop UI check

Launch Jarvis:

```powershell
python scripts/start_jarvis.py
```

Expected:

- Jarvis Ultimate desktop window opens.
- The orb is now centered in the interface.
- Runtime status and events are on the left side.
- Workspace panels are on the right side.
- Conversation is below/around the central orb.
- The orb changes state while Jarvis listens, wakes, responds, and returns to sleep.

## 4. Voice/UI state check

Say:

```text
Hey Jarvis, give me one short sentence.
```

Expected:

- Jarvis wakes.
- The central orb becomes more active.
- Jarvis responds and speaks.
- Chat/events/status panels update.

Then say:

```text
That's all Jarvis.
```

Expected:

- Jarvis returns to sleep mode.
- Orb returns to a calm/sleeping or wake-listening state.

## 5. Cleanup before commit

If everything passes:

```powershell
Remove-Item apply_0_1_6c_central_orb_layout_patch.py
Remove-Item -Recurse patch_files
```

Then commit:

```powershell
git add .
git commit -m "0.1.6c Add central orb UI state engine"
git push
```
