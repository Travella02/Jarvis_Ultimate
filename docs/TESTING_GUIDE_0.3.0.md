# Testing Guide — 0.3.0 Memory Auto-Capture + Candidate Review

## 1. Run the full test suite

From the project root:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## 2. Launch Jarvis

```powershell
python scripts\start_jarvis_app.py
```

## 3. Test automatic candidate capture

Say or type:

```text
Jarvis, from now on, I prefer short direct patch instructions.
```

Then ask:

```text
Jarvis, what memories are waiting for review?
```

Expected result: Jarvis should mention a pending memory candidate about your preference.

## 4. Test approving a candidate

After a candidate exists, say:

```text
Jarvis, save that permanently.
```

Then ask:

```text
Jarvis, what do you remember about patch instructions?
```

Expected result: Jarvis should recall the approved memory naturally.

## 5. Test rejecting a candidate

Create another candidate:

```text
Jarvis, from now on, testing candidate rejection is important.
```

Then say:

```text
Jarvis, reject that.
```

Expected result: Jarvis should reject the latest pending candidate.

## 6. Test automatic short-term capture

Say:

```text
Jarvis, we are testing the memory pipeline right now.
```

Then ask:

```text
Jarvis, what do you remember about testing the memory pipeline?
```

Expected result: Jarvis should be able to recall the short-term testing context.

## 7. Confirm chat archive still works

Ask:

```text
Jarvis, what did we talk about memory?
```

Expected result: Jarvis should summarize recent memory-related conversation naturally instead of dumping raw logs.
