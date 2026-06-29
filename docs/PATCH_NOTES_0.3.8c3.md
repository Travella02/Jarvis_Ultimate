# Jarvis Ultimate 0.3.8c3 — Independent Panel Drag Freeze Hotfix

This hotfix keeps the 0.3.8b–0.3.8c2 workspace stability work intact and only fixes the issue where moving one floating panel could cause another floating panel to jump or reflow.

## What changed

- Added an active panel interaction guard for drag and resize operations.
- Before moving/resizing a panel, Jarvis now freezes the saved layout records for every other panel.
- When the move/resize finishes, Jarvis restores the unaffected panels so only the active panel changes position or size.
- The renderer skips full layout reapplication while a drag/resize is active so bridge refreshes cannot re-sanitize all panel positions mid-drag.
- Responsive layout clamping waits for the active interaction to finish and settle.
- `applyPanelLayout` can preserve specific panel keys so unaffected panels keep their exact positions.
- Updated the app-shell version to `0.3.8c3`.

## Why this matters

Moving the Core Orb panel should never cause the Conversation, Runtime, Workspace, Voice, or Diagnostics panels to snap somewhere else. The last clicked/moved panel can still come to the front, but inactive panels should stay where they are.

## Validation

- `node --check app_shell/renderer/renderer.js`
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 443 tests in 3.482s — OK`
