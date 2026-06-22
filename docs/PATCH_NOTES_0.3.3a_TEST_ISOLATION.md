# Jarvis Ultimate 0.3.3a App Agent Test-Isolation Hotfix

This is a test-only hotfix for the 0.3.3a typed-memory response patch.

## Why this exists

Manual testing showed two failures in `tests/unit/test_app_agent_launch_verification_026.py` when Discord was already installed or running on the local machine.

The runtime behavior was not the problem. The unit tests were accidentally allowing the App Agent launch path to check the real system's running processes. If Discord was already open, Jarvis correctly returned the existing-app focus path, but the tests expected a mocked launch path.

## Changes

- Updated `test_verified_launch_waits_for_expected_process` to patch `_candidate_is_running` as `False`.
- Updated `test_stale_launcher_retries_refreshed_real_app_path` to patch `_candidate_is_running` as `False`.
- Replaced the old hardcoded real user path in the Discord test fixture with a neutral `JarvisTest` path.
- No Jarvis runtime behavior changed.
- No app-shell version bump; the active runtime remains `0.3.3a`.

## Validation

Validated in the patch workspace with:

```powershell
PYTHONPATH=src python -m unittest discover -s tests -v
```

Result:

```text
Ran 374 tests in 4.280s
OK
```
