# Jarvis Ultimate 0.1.9 Testing Guide

## 1. Run the automated tests

From the main project folder:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## 2. Launch the native app shell

```powershell
python scripts\start_jarvis_app.py
```

The app should open as the native Electron Jarvis window.

## 3. Check the new layout

Confirm that:

- The orb is the main center focus.
- Runtime/voice/workspace cards are on the left.
- Conversation is on the right as a dock.
- Diagnostics are collapsed at the bottom by default.
- The top status still shows bridge and voice warmup.

## 4. Check voice readiness

Wait for the voice card to show warmup as ready.

Then test:

1. Click **Listen Once**.
2. Ask: `What is your status?`
3. Jarvis should listen, think, answer, and return to idle.
4. The orb should switch visual states during the flow.

## 5. Check sleep/wake mode

1. Click **Start Sleep/Wake**.
2. Say: `Hey Jarvis, what is your status?`
3. Jarvis should wake, answer, and keep listening.
4. Click **Stop Voice** when done.

## 6. Check diagnostics drawer

Click **Show Diagnostics** at the bottom.

Confirm that:

- The live event stream appears.
- The button changes to **Hide Diagnostics**.
- Clicking it again collapses the diagnostics drawer.

## 7. Common issues

### The UI opens but voice does not work

Check the voice warmup status first. If it is still warming, wait a little longer.

### npm/node errors

The app shell still needs Node.js/npm installed for Electron. Check:

```powershell
node -v
npm -v
```

### The app looks squished

Maximize the window. The layout is responsive, but the best view is a large desktop window.
