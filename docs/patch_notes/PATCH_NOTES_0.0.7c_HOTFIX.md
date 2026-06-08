# Patch Notes — 0.0.7c Kokoro Test Hotfix

## Summary

This hotfix corrects a brittle unit test introduced in 0.0.7c. On machines where Kokoro is installed, the fallback test incorrectly used the real Kokoro provider and failed because Kokoro successfully generated speech instead of falling back to the mock provider.

## What changed

- Updated `tests/unit/test_tts_providers.py` so `test_manager_uses_mock_fallback_when_kokoro_unavailable` explicitly mocks Kokoro as unavailable.
- The test now verifies fallback behavior deterministically whether Kokoro is installed or not.
- No runtime Jarvis behavior was changed.
- No TTS provider behavior was changed.
- No `.env` values were changed.

## Why this was needed

0.0.7c intentionally made Kokoro the default provider. The fallback test was meant to simulate Kokoro being unavailable, but it only assumed Kokoro would not be installed. After installing `requirements-tts.txt`, Kokoro was available, so the test used Kokoro and failed the expected provider check.

## Expected test result

```text
Ran 86 tests
OK
```

## Commit guidance

Apply this hotfix on top of 0.0.7c, rerun the tests and manual Kokoro checks, then commit 0.0.7c after everything passes.
