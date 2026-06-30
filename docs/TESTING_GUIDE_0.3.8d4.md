# Testing Guide — 0.3.8d4 Custom Preset Panel Visibility Restore

## 1. Run unit tests

From the Jarvis project root, run:

```powershell
python -m unittest discover -s tests -v
```

Expected result: all tests pass.

## 2. Start Jarvis

After the tests pass, start the app shell:

```powershell
python scripts\start_jarvis_app.py
```

## 3. Manual UI checks

1. Open Jarvis and create a layout with only two panels visible, such as Core Orb and Conversation.
2. Click `Save Preset` and save it with a clear name.
3. Open several more panels, such as Runtime, Voice, Workspace, and Diagnostics.
4. Select the saved two-panel preset.
5. Confirm the extra panels close and the preset returns to the saved open-panel state.
6. Create another preset with more panels visible.
7. Switch back and forth between the two presets.
8. Confirm each preset restores both geometry and open/closed panel state.
9. Rename a preset and confirm it still applies correctly.
10. Delete a preset and confirm the current layout does not move.

## Success looks like

- A preset saved with two open panels returns to exactly those open panels.
- A preset saved with more open panels reopens those panels when selected.
- Hidden panels do not remain visible after switching to a preset where they were closed.
- Rename/Delete still work.
- Panel drag, resize, maximize/restore, and active-panel priority still behave like 0.3.8d3.
