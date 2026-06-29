# Jarvis Ultimate 0.3.8c4 — Release-Safe Panel Geometry Freeze Hotfix

This hotfix follows 0.3.8c3 after live testing showed that the Conversation panel could still move after releasing the Core Orb panel.

## What changed

- Unaffected panels are now frozen from their real on-screen DOM geometry before a drag or resize begins.
- The frozen geometry is applied immediately to unaffected panels so bridge refreshes, grid reflow, and release-time layout cleanup cannot snap them to an older saved position.
- Preserved floating panel records are sanitized without reintroducing stale geometry.
- Moving the Core Orb panel should not cause the Conversation panel to move after release.
- Resizing one panel should not cause another panel to move after release.
- App shell version is now `0.3.8c4`.

## Files updated

- `app_shell/renderer/renderer.js`
- `app_shell/renderer/styles.css`
- `src/jarvis/clients/app_shell/bridge.py`
- App-shell version assertion tests
- `tests/unit/test_app_shell_dom_geometry_freeze_038c4.py`
- `JARVIS_ULTIMATE_HANDOFF_INSTRUCTIONS.md`

## Validation

Validated in the patch workspace with:

```powershell
node --check app_shell/renderer/renderer.js
python -m unittest discover -s tests -v
```

Result:

```text
Ran 446 tests in 3.529s
OK
```
