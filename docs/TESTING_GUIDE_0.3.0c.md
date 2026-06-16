# Testing Guide — 0.3.0c Local API Disconnect Guard Hotfix

## 1. Run the full test suite

From the Jarvis project root:

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

Leave the native app shell open for a few minutes while it polls the Python bridge.

Check the terminal. You should no longer see repeated tracebacks like:

```text
ConnectionAbortedError: [WinError 10053]
BrokenPipeError
ConnectionResetError
```

Occasional PyTorch/Kokoro warnings are separate dependency warnings and are not fixed by this patch.

## 4. Voice sanity check

Say a normal wake command and make sure Jarvis still responds:

```text
Jarvis, what is your status?
```

This patch should not change voice behavior.
