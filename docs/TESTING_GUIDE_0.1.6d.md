# Testing Guide — 0.1.6d Advanced Solid Orb Renderer

## 1. Run tests
From the Jarvis Ultimate root with the venv active:

```powershell
python -m unittest discover -s tests -v
```

Success should show all tests passing.

## 2. Boot check
```powershell
python scripts/run_jarvis.py
```

Expected:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 3. Desktop UI check
```powershell
python scripts/start_jarvis.py
```

Confirm:
- The Jarvis Ultimate desktop opens.
- The orb is centered.
- The orb now looks more solid/dimensional instead of only flat rings.
- The orb has rotating rings and particle accents.
- The state label says something like `SOLID ORB RENDERER · STATE-REACTIVE CORE`.

## 4. Voice-state check
Say:

```text
Hey Jarvis, give me one short sentence.
```

Confirm:
- Jarvis wakes up.
- The orb changes state while listening/thinking/speaking.
- Jarvis speaks the response.
- Saying `that's all Jarvis` returns him to sleep mode.

## 5. Commit only after success
If tests pass and the UI works:

```powershell
Remove-Item apply_0_1_6d_advanced_solid_orb_patch.py
Remove-Item -Recurse patch_files

git add .
git commit -m "0.1.6d Add advanced solid orb renderer"
git push
```
