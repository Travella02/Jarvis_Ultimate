# Jarvis Ultimate 0.1.8 Testing Guide

## 1. Apply the patch

From your main Jarvis project folder, run:

```powershell
python apply_0_1_8_voice_state_bridge_patch.py
```

## 2. Run the test suite

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

The tested package produced:

```text
Ran 201 tests in 2.616s
OK
```

## 3. Launch the app shell

Run:

```powershell
python scripts\start_jarvis_app.py
```

If Electron is already installed from 0.1.7, the native Jarvis app should open.

If Electron dependencies are missing, run:

```powershell
cd app_shell
npm install
cd ..
python scripts\start_jarvis_app.py
```

## 4. Manual checks

Inside the Jarvis app window:

1. Confirm the orb loads and shows **Bridge Online**.
2. Type a normal command in the text box and press **Send**.
3. Press **Listen Once**.
4. Say a short command such as:

```text
What is your status?
```

5. Jarvis should listen, transcribe, think, speak, and then return to ready/error depending on your local STT/TTS setup.
6. Press **Start Sleep/Wake**.
7. Say a wake phrase and command, for example:

```text
Hey Jarvis, what is your status?
```

8. Press **Stop Voice** to stop sleep/wake mode.

## 5. What success looks like

- The UI launches as a real desktop app.
- The bridge says **Bridge Online**.
- The voice status card changes from idle to running while voice mode is active.
- The orb changes states while Jarvis listens, thinks, and speaks.
- Recent heard text appears in the voice status card and conversation log.
- The Event Stream shows voice/app-shell events.

## 6. Common issues

### `npm` or `node` is not recognized

Node.js is not installed or your terminal PATH has not refreshed. Install Node.js LTS, close/reopen your terminal or coding app, then check:

```powershell
node -v
npm -v
```

### The Stop Voice button does not stop instantly

That is expected if Jarvis is currently recording microphone audio. Stop requests are honored at the next safe checkpoint after the current listen/transcription call returns.

### The UI opens but voice does not hear anything

Check your existing voice setup:

```powershell
python scripts\run_jarvis_voice.py
```

Also test STT status from the normal CLI if needed:

```text
stt status
listen once
```

