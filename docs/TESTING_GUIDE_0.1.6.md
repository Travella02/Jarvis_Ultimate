# Testing Guide — 0.1.6 Desktop UI + Avatar Workspace Foundation

## 1. Apply the patch
From the Jarvis Ultimate root:

```powershell
python apply_0_1_6_desktop_ui_avatar_workspace_patch.py
```

## 2. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 165 tests
OK
```

The exact runtime may vary.

## 3. Boot check

```powershell
python scripts/run_jarvis.py
```

Expected:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 4. CLI still works

```powershell
python scripts/run_cli.py
```

Try:

```text
status
wake status
voice loop status
exit
```

This confirms the UI patch did not break the headless/CLI path.

## 5. Launch the desktop UI

```powershell
python scripts/run_desktop.py
```

Expected:
- A `Jarvis Ultimate` desktop window opens.
- You see an orb/avatar placeholder.
- You see chat, status, workspace, and event panels.
- The UI shows registered agents and runtime/provider status.

## 6. Send a typed command in the desktop UI
In the UI command box, type:

```text
hello jarvis
```

Then press Enter or click Send.

Expected:
- Your message appears in the chat panel.
- Jarvis's response appears in the chat panel.
- The event panel updates.
- The avatar state changes while the command is handled.

If LM Studio is closed, Jarvis may show an LLM/provider connection error. That is not a UI failure; start LM Studio and try again.

## 7. Confirm modular panel foundation
The Workspace panel should list future drop-in panel ideas such as:
- reminders
- web results
- generated images
- files
- screen/OCR context
- agent dashboards

0.1.6 does not implement those tools yet. It creates the UI foundation so they can be added later.

## 8. Cleanup after success

```powershell
Remove-Item apply_0_1_6_desktop_ui_avatar_workspace_patch.py
Remove-Item -Recurse patch_files
```

## 9. Commit after tests and manual UI check pass

```powershell
git add .
git commit -m "0.1.6 Add desktop UI avatar workspace foundation"
git push
```
