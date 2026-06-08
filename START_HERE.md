# Start Here

This is the clean Jarvis 3 project skeleton.

## What to do

1. Extract this folder somewhere separate from your current Jarvis project.
2. Open PowerShell inside `Jarvis_3`.
3. Create and activate the virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

4. Run the current placeholder entrypoint:

```powershell
python scripts/run_jarvis.py
```

5. Run tests:

```powershell
python -m unittest discover -s tests -v
```

The next coding milestone should be:

`0.1.0 — Core Boot + Agent Registry + Event System`
