# Patch Notes — 0.2.7a App Alias Test Compatibility Hotfix

## Summary
This hotfix updates one older app-discovery unit test so it stays stable with the new 0.2.7 behavior where Jarvis may focus an already-running app instead of launching another copy.

## Changed
- Updated the Chrome/Google browser fast-path unit test to explicitly simulate Chrome not already running.
- Preserves the 0.2.7 App Agent alias/role behavior.
- Keeps unit tests from depending on which apps are currently running on the developer machine.

## Notes
- This does not change normal Jarvis behavior.
- The visible app-shell version remains 0.2.7 to avoid breaking version-sensitive UI tests.
