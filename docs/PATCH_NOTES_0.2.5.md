# Jarvis Ultimate 0.2.5 — App Discovery Speed + Caption Sync

## Added
- Background app index warmup now starts correctly from the app shell runtime config.
- Faster app-discovery cache behavior for general installed apps, not only specific known apps.
- Discord launcher improvements, including versioned `Discord.exe` detection before `Update.exe` fallback.
- Faster adaptive app-shell refresh while Jarvis is listening, thinking, or speaking.
- Faster caption typewriter catch-up for short app/tool responses.

## Fixed
- Fixed app-index warmup bug caused by using `self.config` / `self.events` instead of `self.runtime.config` / `self.runtime.events`.
- Improves cases where Jarvis says an app opened but the launcher was only an updater path.
- Reduces delay where Jarvis finishes speaking before the caption starts typing.

## Notes
- Unit tests should still avoid opening real apps.
- First launch after the patch may rebuild the app index once, then repeated app commands should be faster.
