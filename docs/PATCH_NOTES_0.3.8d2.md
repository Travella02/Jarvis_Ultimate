# Jarvis Ultimate 0.3.8d2 — Save Preset Name Dialog Hotfix

This is a focused hotfix for the 0.3.8d Save Custom Layout Preset feature.

## What changed

- Replaced the unreliable native `window.prompt()` save-preset naming flow with a visible in-shell Jarvis dialog.
- Clicking **Save Preset** now opens a centered modal where you can name the current layout.
- The dialog supports:
  - typing a custom preset name,
  - pressing **Enter** to save,
  - clicking **Cancel** to cancel,
  - pressing **Escape** to cancel,
  - clicking outside the dialog to cancel.
- Saved presets still appear under the **Custom** group in the Layouts dropdown.
- Existing 0.3.8d behavior remains intact:
  - custom presets save panel position, size, floating/docked state, minimized state, and z-order,
  - saved presets scale back into the current workspace on maximize/restore,
  - panel drag/release stability from 0.3.8c4 remains unchanged.
- The app-shell runtime version remains **0.3.8d** so existing version-pinned tests stay aligned.

## Why this patch was needed

The first 0.3.8d save-preset flow relied on the browser-native prompt dialog. In the Electron desktop shell, that prompt may not appear reliably, which made the feature look like nothing happened and prevented you from naming presets.

## Validation

Validated with:

```powershell
node --check app_shell/renderer/renderer.js
python -m unittest discover -s tests -v
```

Result:

```text
Ran 454 tests in 4.479s
OK
```
