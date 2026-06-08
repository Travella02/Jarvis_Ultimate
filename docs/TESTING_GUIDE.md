# Testing Guide

After extracting the zip:

```powershell
cd Jarvis_3
python -m venv .venv
.venv\Scripts\activate
python -m unittest discover -s tests -v
```

At this stage, the project is mostly structure and placeholders. The test suite may report 0 tests until the first coding milestone is added.

Expected first real milestone:
- Core result object
- Event bus
- Agent registry
- Mock agent
- Basic router test
