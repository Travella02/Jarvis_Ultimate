# Testing Guide — 0.1.2a Smart Listen Endpointing Hotfix

Run these commands from the Jarvis Ultimate root with the virtual environment active.

## 1. Run tests

```powershell
python -m unittest discover -s tests -v
```

Expected:

```text
Ran 139 tests
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

## 3. Manual CLI check

```powershell
python scripts/run_cli.py
```

Run:

```text
stt listen settings
listen faster
listen once
stt debug last
```

Say a short phrase like:

```text
Hey Jarvis
```

Expected:

- Jarvis should stop shortly after you stop speaking.
- Audio duration should usually be around 1–3 seconds for a short phrase.
- `stt debug last` should show `Stop reason: silence_detected`.
- Debug output should show `Effective energy threshold`, `Peak RMS`, and `Adaptive energy`.

## 4. If Jarvis still records too long

Run:

```text
stt energy 0.03
listen once
stt debug last
```

If it still records too long, try:

```text
stt energy 0.04
listen once
```

## 5. If Jarvis cuts you off

Run:

```text
listen balanced
```

or:

```text
listen safer
```

## 6. Wake voice check

Run:

```text
wake voice once
```

Say:

```text
Hey Jarvis, give me one short sentence.
```

Expected:

- Jarvis hears the command.
- Jarvis responds.
- Jarvis speaks the response.

Only commit after tests pass and the manual listening behavior is better than 0.1.2.
