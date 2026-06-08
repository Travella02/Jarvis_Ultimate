# Testing Guide — Jarvis Ultimate 0.0.3

## 1. Install the patch

From your Jarvis project root:

```powershell
python apply_0_0_3_lm_studio_conversation_patch.py
```

## 2. Run boot test

```powershell
python scripts/run_jarvis.py
```

Expected:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 3. Run automated tests

```powershell
python -m unittest discover -s tests -v
```

Expected:

```text
OK
```

The internal clean-room patch test passed 21 tests.

## 4. Start LM Studio

In LM Studio:

1. Open LM Studio.
2. Load the local model you want Jarvis to use.
3. Start the Local Server.
4. Confirm it is using the default local API URL:

```text
http://localhost:1234/v1
```

## 5. Run CLI chat

```powershell
python scripts/run_cli.py
```

Try:

```text
hello jarvis
what are you able to do right now?
status
list agents
screen check
exit
```

Expected behavior:

- Normal chat should use LM Studio.
- `status` should show the provider as `lm_studio`.
- `list agents` should still list registered agents.
- `screen check` should still route to the Screen Agent placeholder.
- If LM Studio is not running, Jarvis should clearly say it could not connect.

## 6. Commit only after success

After tests pass and the CLI works:

```powershell
git status
git add .
git commit -m "0.0.3 Add LM Studio conversation provider"
git push
```

You can delete the installer and `patch_files/` before committing if you do not want them in the repo.
