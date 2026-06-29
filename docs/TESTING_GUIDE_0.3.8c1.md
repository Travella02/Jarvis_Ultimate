# Testing Guide — Jarvis Ultimate 0.3.8c1

## 1. Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_8c1_window_state_panel_follow_patch.py
```

## 2. Run automated tests

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

## 3. Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

## 4. Manual checks

### Window maximize / restore

1. Start Jarvis normally.
2. Move the Runtime, Workspace, Conversation, or Core Orb panel.
3. Resize one floating panel.
4. Maximize the Jarvis window.
5. Restore the Jarvis window back down.
6. Try shrinking and expanding the window manually.

Success looks like:

- Floating panels follow the new window size.
- Panels do not stay stuck in the old maximized/restored position.
- Panels stay reachable inside the visible app window.
- Panels do not explode, overlap unexpectedly, or disappear off-screen.

### Active panel priority

1. Put two floating panels near each other or slightly overlapping.
2. Click one panel.
3. Click the other panel.
4. Drag a panel.

Success looks like:

- The panel you clicked or moved most recently appears in front.
- Dragged/resized panels stay visually on top during the interaction.

### Runtime content containment

1. Float the Runtime panel.
2. Try shrinking it.
3. Watch the LLM/STT/TTS/Agents rows.

Success looks like:

- The Runtime panel should not shrink so small that the contents spill outside.
- Long LLM model names should wrap or scroll inside the panel instead of drawing outside it.

### Existing controls

Confirm these still work:

- Lock
- Min
- Dock
- Pop
- Reset Layout
- Layout presets
- Dropdown text remains readable

## Common issues

If panels still look wrong after applying the patch, first click **Reset Layout** inside Jarvis. The hotfix scales saved floating layouts, but an old extreme saved layout can still be easier to clear manually.

If a panel is intentionally minimized, it may stay short. That is expected. The minimum-size guard applies to restored panels, not minimized panels.
