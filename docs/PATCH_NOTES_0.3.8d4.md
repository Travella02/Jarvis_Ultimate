# Jarvis Ultimate 0.3.8d4 — Custom Preset Panel Visibility Restore

This hotfix keeps the working custom preset rename/delete behavior from `0.3.8d3` and fixes the remaining preset restore issue.

## Issue fixed

Custom presets restored panel positions and sizes, but they did not restore which panels were open or closed when the preset was saved.

That meant a preset saved with only two panels open could still leave extra panels open when applied later.

## Changes

- Custom presets now save panel visibility state along with layout geometry.
- Saved visibility covers Runtime, Voice, Workspace, Conversation, and Diagnostics panels.
- Applying a preset now restores the saved open/closed panel state.
- If a preset was saved with fewer panels open, applying it closes the panels that were not open in the preset.
- If a preset was saved with more panels open, applying it opens those panels again.
- Existing older presets without visibility data still apply safely and preserve current panel visibility.
- Rename and Delete preset behavior remains unchanged.
- App shell version is now `0.3.8d4`.

## Validation

- `node --check app_shell/renderer/renderer.js`
- `PYTHONPATH=src python -m unittest discover -s tests -v`
- Result: `Ran 461 tests in 3.941s — OK`
