# Testing Guide — 0.2.1 Orb Realism + Caption/Transition Polish

## 1. Run the test suite

From the Jarvis project root:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## 2. Launch the app shell

```powershell
python scripts\start_jarvis_app.py
```

## 3. Visual checks

Check these manually:

1. Background should be almost pure black.
2. Panels should mostly be transparent with blue holographic edges.
3. Sleep mode should be grey, but not so dark that the orb disappears.
4. Sleep mode should still breathe and the rings/particles should move slowly.
5. The center orb should look more like a realistic 3D sphere, not a bullseye.
6. Switching between sleep/listening/thinking/speaking should fade smoothly.
7. Rings and floating particles should not jump to new angles or positions between states.
8. Speaking should use ring speed/color changes, not outward wave rings.
9. Spoken text should appear centered under Jarvis without a box or `Jarvis Output` label.
10. A new Jarvis response should clear the previous caption before typing the new one.
11. Orb Only mode should show only Jarvis and the spoken caption.
12. Press Escape to leave Orb Only mode.

## 4. Sleep acknowledgement checks

With sleep/wake running, try:

- `Thank you, Jarvis.`
- `Thanks, Jarvis.`
- `That's all, Jarvis.`

Jarvis should no longer say `Going back to sleep, sir.`

Expected natural behavior:

- For thanks: `Of course, sir.` then sleep.
- For closure phrases: `Okay, sir.` then sleep.
- No extra sleep-mode announcement should be spoken.
