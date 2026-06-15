# Jarvis Ultimate 0.2.6b — App Alias Routing + Chat Scroll Hotfix

## Fixes

- Routes commands like `when I say music, open Spotify` to the App Agent instead of normal conversation.
- Keeps learned app aliases higher priority than discovered app guesses, so `open music` can use the taught Spotify alias instead of falling through to Media Player.
- Adds safer Media Player process aliases so Jarvis has a better chance of closing it if it was opened by mistake.
- Fixes conversation panel scrolling so manual scrolling is not constantly forced back to the newest chat message.
- Adds app-shell capabilities for manual chat scroll preservation and app alias teaching routing.

## Notes

Resizable panels are intentionally deferred to a later UI-specific update so this hotfix can stay focused on App Agent reliability and the chat-scroll bug.
