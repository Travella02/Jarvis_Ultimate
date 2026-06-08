# Jarvis Ultimate 0.0.2 Testing Guide

Run all commands from the root of your `Jarvis_Ultimate` project.

## 1. Activate your virtual environment

```powershell
.venv\Scripts\activate
```

## 2. Run Jarvis boot test

```powershell
python scripts/run_jarvis.py
```

Expected success:

```text
Jarvis 3 is online. Registered 9 agents.
```

The exact number can be higher later if more agents are added.

## 3. Run the CLI

```powershell
python scripts/run_cli.py
```

Try these commands:

```text
hello
status
list agents
screen check
open chrome
change your voice
change your avatar
exit
```

Expected behavior:

- `hello` gives a normal Jarvis response through the new routing system.
- `status` says Jarvis core is online.
- `list agents` lists the registered agents.
- `screen check` routes to the Screen Agent placeholder.
- `open chrome` routes to the App Agent placeholder.
- `change your voice` routes to the Voice Agent placeholder.
- `change your avatar` routes to the Avatar Agent placeholder.

Placeholder responses are expected. Real tools come later.

## 4. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Expected success:

```text
OK
```

This patch currently includes 14 tests.

## 5. Check logs

After running Jarvis, check:

```text
logs/brain/events.jsonl
logs/brain/results.jsonl
```

Expected success:

- The files exist.
- They contain JSON lines for boot, routing, selected agents, and results.

## Common issues

### ModuleNotFoundError: No module named 'jarvis'

Run:

```powershell
python -m pip install -e .
```

Or use the scripts provided in `scripts/`, which now add `src` to the Python path automatically.

### No tests ran

Make sure you are in the project root and that the patch installed the test files into `tests/unit/` and `tests/integration/`.

### Placeholder response

That is expected for most agents in 0.0.2. This update creates routing and structure, not real screen/app/voice tools yet.
