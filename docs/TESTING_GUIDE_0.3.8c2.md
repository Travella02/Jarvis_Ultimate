# Jarvis Ultimate 0.3.8c2 Testing Guide

This guide verifies the maximize/restore panel scaling hotfix.

## 1. Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_8c2_workspace_safe_scaling_patch.py
```

## 2. Run the test suite

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

1. Open Jarvis in its normal window size.
2. Move the Core, Conversation, Runtime, or Workspace panels into floating positions.
3. Maximize the Jarvis window.
4. Restore the Jarvis window back down.
5. Repeat maximize/restore a few times.

Success should look like this:

- Floating panels stay below the top control bar.
- Floating panels keep roughly the same relative layout proportions.
- Panels do not cover the Jarvis title/top-control panel after restore.
- Panels remain reachable and clamped inside the workspace.
- The last clicked or moved panel still comes to the front.
- Runtime text stays contained inside the Runtime panel.

## 5. If an older saved layout still looks strange

Click **Reset Layout** once inside Jarvis, then repeat the maximize/restore test. This patch uses a new workspace viewport key, but Reset Layout is still useful if the saved panel positions themselves were created during an earlier broken layout test.
