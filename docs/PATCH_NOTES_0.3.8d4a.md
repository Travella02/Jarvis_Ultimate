# Jarvis Ultimate 0.3.8d4a — Preset Visibility Installer Fix

This is a tiny installer-only hotfix for the 0.3.8d4 preset panel visibility restore patch.

## Fix

- Corrected the installer script string escaping issue that caused `SyntaxError: unterminated string literal` before the patch could apply.
- Keeps the 0.3.8d4 runtime behavior unchanged.
- Includes the full 0.3.8d4 patch payload so you can apply this package directly instead of the broken installer package.

## Runtime behavior from 0.3.8d4

- Custom presets save which panels were open/closed.
- Switching presets restores the saved open/closed panel state.
- Rename and Delete preset behavior remains intact.

## Validation

- Installer compiled successfully with Python.
- Renderer JavaScript syntax check passed.
