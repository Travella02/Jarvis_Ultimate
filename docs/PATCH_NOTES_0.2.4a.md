# Jarvis Ultimate 0.2.4a — General App Discovery Speed Hotfix

## Fixed

- Fixed the Snipping Tool speed test so it no longer fails on machines where Windows exposes the launcher as `SnippingTool.exe`.
- Canonical known-app matches now keep the human app name, such as `snipping tool`, even when the launcher file is named differently.
- Clears the stale app index by bumping the app index version.

## Improved

- Added a fast general app discovery pass before deep scanning.
- The fast pass checks cheap launcher sources first: learned aliases, built-in aliases, known paths, registry App Paths, PATH, Start Menu shortcuts, desktop shortcuts, and WindowsApps.
- Deep Program Files scanning is now treated as a fallback/background behavior instead of the first thing Jarvis relies on for unknown apps.
- This is a better foundation for future SaaS-style use because Jarvis can discover apps on different Windows machines without needing every app hardcoded.

## Notes

- The first launch of a completely unknown app can still be slower if it is not exposed through the Start Menu, registry, PATH, WindowsApps, or desktop shortcuts.
- After Jarvis successfully opens an app once, he learns the alias/path so the next launch should be faster.
