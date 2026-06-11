# Testing Guide - 0.1.9b2

Run from the Jarvis_Ultimate project root.

## Automated tests

```powershell
python -m unittest discover -s tests -v
```

Expected result: all tests pass.

## Manual checks

1. Launch Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

2. Let Jarvis auto-enter sleep/wake mode.
3. Confirm the background is nearly black.
4. Confirm the panels look more transparent/holographic blue.
5. Confirm sleep mode stays one dim grey color.
6. Confirm the rings still rotate slowly while Jarvis is sleeping.
7. Confirm the orb still breathes subtly while sleeping.
8. Wake Jarvis and ask a question.
9. Confirm transitions between sleep/listening/thinking/speaking fade instead of snapping.
10. Confirm speaking uses ring speed/color changes without outward voice waves.
