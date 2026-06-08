# Testing Guide — 0.0.9c Low-Latency Listen Mode

Run all commands from the Jarvis Ultimate project root with the venv active.

## 1. Apply the patch

```powershell
python apply_0_0_9c_low_latency_listen_patch.py
```

## 2. Install/update STT requirements

```powershell
python -m pip install -r requirements-stt.txt
```

## 3. Run automated tests

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 112 tests
OK
```

## 4. Boot check

```powershell
python scripts/run_jarvis.py
```

Expected result:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 5. Manual CLI checks

```powershell
python scripts/run_cli.py
```

Run:

```text
stt status
stt listen settings
stt warmup
listen once
stt debug last
```

Success signs:

```text
listen mode: smart
Listen mode: smart
Stop reason: silence_detected
Heard: <what you said>
```

## 6. Tune speed vs cutoff

Try faster endpointing:

```text
listen smart max 8 silence 0.8
```

If Jarvis cuts you off, try:

```text
listen smart max 8 silence 1.2
```

For strict timer comparison:

```text
listen fixed 2
```

## 7. What common issues mean

- `No speech detected before smart-listen start timeout`: Jarvis did not hear audio above the energy threshold. Try speaking louder, check the mic, or lower `JARVIS_STT_ENERGY_THRESHOLD`.
- Jarvis stops too early: increase `JARVIS_STT_SILENCE_SECONDS`.
- Jarvis waits too long after you finish: decrease `JARVIS_STT_SILENCE_SECONDS`.
- Keyboard/fan noise triggers listening: increase `JARVIS_STT_ENERGY_THRESHOLD` or use a better mic/noise setup.

## 8. Commit guidance

Only commit after:

1. Tests pass.
2. `listen once` records/transcribes successfully.
3. At least one smart listen test stops after speech instead of waiting for a long fixed timer.

Suggested commit:

```powershell
git add .
git commit -m "0.0.9c Add low-latency smart listen mode"
git push
```
