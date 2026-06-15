# Testing Guide — 0.2.6a

## Automated tests

From the project root, run:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
OK
```

No real apps should open during the test run. In particular, Notepad should not open from `test_app_file_abilities_030.py`.

## Manual app-agent smoke test

After the unit tests pass, launch Jarvis:

```powershell
python scripts\start_jarvis_app.py
```

Try:

```text
Jarvis, open calculator
Jarvis, close calculator
Jarvis, open Chrome
Jarvis, close Chrome
Jarvis, open Discord
Jarvis, close Discord
```

Jarvis should still open and close apps normally outside the test suite.
