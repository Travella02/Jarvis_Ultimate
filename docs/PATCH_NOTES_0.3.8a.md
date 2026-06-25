# Jarvis Ultimate 0.3.8a — Panel Lock Only

## Purpose

This is a deliberately small UI stabilization patch after resetting back to the 0.3.8 dockable workspace baseline.

It only adds per-panel locking. It does not change layout scaling, popout behavior, preset math, or responsive window sizing.

## Changes

- Added a per-panel **Lock** button beside the existing panel layout buttons.
- Added local persistent storage for individual panel locks.
- Locked panels can still be used normally, but they cannot be dragged or resized until unlocked.
- Locked panels show a subtle active lock state so it is clear which panels are protected.
- The global layout lock remains unchanged.
- Added source-level tests for the new lock storage, button action, drag/resize guard, CSS locked state, and app-shell capability.

## Manual check

Start Jarvis, unlock the global layout, then lock one panel. Try dragging or resizing that locked panel. It should stay in place. Other unlocked panels should still be movable.

## Validation

Test command used:

```powershell
python -m unittest discover -s tests -v
```

Result in patch workspace:

```text
Ran 427 tests in 4.498s

OK
```
