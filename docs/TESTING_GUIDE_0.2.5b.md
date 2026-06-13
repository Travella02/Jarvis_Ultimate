# Testing Guide — 0.2.5b Caption Version Test Fix

## 1. Run the full tests

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

## 3. Manual check

Try:

```text
Jarvis, open calculator
Jarvis, close calculator
```

The caption under the orb should still begin typing while Jarvis is speaking, not only after he has returned to listening.
