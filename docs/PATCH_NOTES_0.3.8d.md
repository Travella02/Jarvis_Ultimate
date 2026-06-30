# Jarvis Ultimate 0.3.8d — Save Custom Layout Preset

## Purpose

This patch adds the next planned workspace feature after the 0.3.8c4 stability checkpoint: saving the current dockable panel layout as a custom selectable preset.

## Changes

- Added a **Save Preset** button in the top workspace controls.
- The button prompts for a custom preset name.
- Saved presets are stored locally in app-shell `localStorage`.
- Custom presets appear under a **Custom** group inside the existing **Layouts** dropdown.
- Custom presets capture panel mode, position, size, minimized state, popped marker, and z-order metadata.
- Custom presets store the workspace viewport snapshot and scale back into the current workspace when applied.
- Reusing the same preset name asks before overwriting it.
- Keeps the 0.3.8c4 drag/release geometry freeze behavior intact.
- Updates the app-shell version to `0.3.8d`.

## New capabilities

- `custom_workspace_layout_presets`
- `user_saved_layout_preset_button`
- `viewport_scaled_custom_layout_restore`

## Files changed

- `app_shell/renderer/index.html`
- `app_shell/renderer/renderer.js`
- `app_shell/renderer/styles.css`
- `src/jarvis/clients/app_shell/bridge.py`
- `tests/unit/test_app_shell_custom_layout_presets_038d.py`
- existing version assertion tests
- `JARVIS_ULTIMATE_HANDOFF_INSTRUCTIONS.md`
