# Testing Guide — 0.0.9a STT Windows Path Hotfix

## 1. Apply the patch
From the Jarvis Ultimate root:

```powershell
python apply_0_0_9a_stt_windows_path_hotfix_patch.py
```

## 2. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Success should show all tests passing. The previous failure should be gone:

```text
test_format_record_result_includes_output ... ok
```

## 3. Smoke test Jarvis

```powershell
python scripts/run_jarvis.py
python scripts/run_cli.py
```

In the CLI:

```text
stt status
stt providers
```

## 4. Commit only after tests pass

```powershell
git add .
git commit -m "0.0.9a Fix STT Windows path formatting test"
git push
```
