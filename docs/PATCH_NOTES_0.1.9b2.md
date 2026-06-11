# Jarvis Ultimate 0.1.9b2 - Holographic Motion Add-on

This is an add-on patch meant to be applied after 0.1.9b and before committing that UI hotfix.

## Changes

- Keeps sleep mode dim grey while restoring slow orbital ring motion.
- Adds a more noticeable slow breathing motion while Jarvis is asleep.
- Removes outgoing speaking waves so speaking is represented by color and ring motion instead.
- Slows and smooths visual state blending between sleep, idle, listening, speaking, thinking, and error.
- Darkens the app background closer to pitch black.
- Makes panels and inputs more transparent blue/holographic.
- Resets app-shell panel storage keys to avoid stale local layout state.

## Notes

This does not change the Python voice pipeline behavior. It is a visual/app-shell refinement only.
