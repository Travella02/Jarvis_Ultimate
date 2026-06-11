# Testing Guide — 0.1.6b Futuristic UI Theme + Panel System

Run these commands from the Jarvis Ultimate project root with the venv active.

## 1. Unit/integration tests

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 170+ tests
OK
```

The exact count may vary if additional local tests exist.

## 2. Boot check

```powershell
python scripts/run_jarvis.py
```

Expected result:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 3. Desktop UI check

```powershell
python scripts/start_jarvis.py
```

Expected manual results:

1. The Jarvis Ultimate desktop window opens.
2. The UI looks more futuristic than 0.1.6a.
3. The avatar/orb panel is larger and state-reactive.
4. The status, chat, workspace, and event panels are visible.
5. The workspace panel lists future drop-in panel types such as web results, reminders, generated images, files, screen context, and agent dashboards.
6. If desktop auto-start voice is enabled, Jarvis starts in sleep/wake mode.
7. Say: `Hey Jarvis, give me one short sentence.`
8. Confirm the chat/event/status panels update and Jarvis speaks.

## 4. Headless CLI still works

```powershell
python scripts/run_cli.py
```

Try:

```text
status
hello jarvis
```

Expected result: CLI still works. The UI patch must not make Jarvis desktop-only.

## 5. Cleanup after successful testing

```powershell
Remove-Item apply_0_1_6b_futuristic_ui_theme_panel_patch.py
Remove-Item -Recurse patch_files
```

## 6. Commit after tests pass

```powershell
git add .
git commit -m "0.1.6b Add futuristic UI theme and panel system"
git push
```
