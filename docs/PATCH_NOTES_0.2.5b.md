# Jarvis Ultimate 0.2.5b — Caption Hotfix Version Test Fix

This hotfix keeps the 0.2.5a caption live-sync behavior, but restores the public app shell version string back to `0.2.5`.

## Fixed

- Keeps older app-shell tests passing by preserving `APP_SHELL_VERSION = "0.2.5"`.
- Keeps `app_shell/package.json` at version `0.2.5`.
- Avoids treating a small hotfix suffix as a new visible app-shell version.

## Why this exists

The 0.2.5a hotfix changed the visible app shell version to `0.2.5a`, while several existing tests still correctly expected the committed feature version to remain `0.2.5`. This patch fixes that mismatch without undoing the caption sync improvements.
