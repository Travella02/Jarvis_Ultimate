# Jarvis Ultimate 0.3.8d3 — Custom-Only Layout Preset Management

This patch removes the built-in Gaming/Coding/Music/Minimal layout presets and turns layout presets into a user-owned preset system.

## Changes

- Removed built-in layout preset options from the Layouts dropdown.
- Kept the Save Preset workflow from 0.3.8d2.
- Added Rename and Delete controls for saved custom presets.
- Rename opens the same visible Jarvis-styled name dialog instead of relying on a hidden native prompt.
- Delete uses a visible Jarvis-styled confirmation dialog instead of relying on a native browser confirmation.
- Custom presets remain local in Electron/Chromium `localStorage`.
- There is no hard-coded preset cap; users can create as many saved layouts as local storage reasonably supports.
- Custom preset names can now use names that previously belonged to built-in presets, such as Gaming or Coding.
- Selecting a custom preset keeps it selected so it can be renamed or deleted immediately.
- Existing saved custom presets are preserved because the storage key is unchanged.
- App shell version is now `0.3.8d3`.

## Validation

- `node --check app_shell/renderer/renderer.js`
- `python -m unittest discover -s tests -v`

## Manual testing focus

- Confirm the dropdown no longer shows Gaming, Coding, Music, or Minimal by default.
- Save multiple custom presets with different names.
- Select a saved preset and confirm it restores the layout.
- Rename a selected saved preset and confirm it keeps the same layout.
- Delete a selected saved preset and confirm it disappears without moving the current panels.
