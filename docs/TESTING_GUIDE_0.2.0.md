# Testing Guide — Jarvis Ultimate 0.2.0

## 1. Run automated tests

From the Jarvis project root:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## 2. Confirm Jarvis runtime still boots

```powershell
python scripts\run_jarvis.py
```

Expected result should include:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 3. Launch the native app shell

```powershell
python scripts\start_jarvis_app.py
```

## 4. Manual UI checks

Check these items in the Jarvis window:

1. The background should be very close to black.
2. Panels should be mostly transparent with blue holographic edges.
3. Sleep mode should stay grey but still breathe and move slowly.
4. Switching states should not glitch the ring positions.
5. Rings and floating points should keep the same orientation path while only color and speed change.
6. Speaking should not show outward wave rings.
7. While Jarvis speaks, the text under the orb should type out in a futuristic caption.
8. Orb Only mode should hide the state label, status line, bridge strip, panels, and diagnostics.
9. Press Escape to exit Orb Only mode.

## 5. Voice flow check

With Auto Wake on:

1. Wait for warmup to show ready.
2. Say the wake phrase.
3. Ask Jarvis a short question.
4. Watch the orb transition from sleep to listening/thinking/speaking.
5. Confirm the under-orb caption types Jarvis's response while or after he speaks.
