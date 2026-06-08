# Testing Guide — 0.0.8 Spoken Response Pipeline

Run every command from the Jarvis Ultimate root with your `.venv` active.

## 1. Apply the patch

```powershell
python apply_0_0_8_spoken_response_pipeline_patch.py
```

Expected: the installer lists updated files and ends with `Patch installed.`

## 2. Install/update TTS requirements if needed

If this machine has not installed the Kokoro TTS requirements yet:

```powershell
python -m pip install -r requirements-tts.txt
```

## 3. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Expected:

```text
Ran 94 tests
OK
```

The exact runtime can vary depending on installed TTS dependencies.

## 4. Boot check

```powershell
python scripts/run_jarvis.py
```

Expected:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 5. Manual CLI voice checks

```powershell
python scripts/run_cli.py
```

Run:

```text
tts status
voice status
tts queue
voice on
```

Expected:

- `tts status` shows Kokoro as the preferred provider.
- `voice status` includes `Spoken response pipeline status`.
- `voice on` says normal chat responses will be sent to the spoken response
  queue.

## 6. Normal spoken chat check

With LM Studio running and a model loaded, run:

```text
hello jarvis, give me one short sentence
```

Expected:

- Text still streams in the CLI.
- Jarvis speaks the response through Kokoro when playback is supported.
- The CLI does not wait for a blocking `Jarvis voice:` result after the message.

Then run:

```text
tts queue status
```

Expected: queue status shows pending/active/completed counters.

## 7. Stop check

Run:

```text
tts stop
voice off
```

Expected:

- `tts stop` reports how many pending chunks were cleared.
- `voice off` disables auto-speak/playback and clears pending speech.

## 8. Commit guidance

Only commit after:

- full tests pass,
- `python scripts/run_jarvis.py` boots,
- `voice on` works,
- one normal LM Studio response speaks or at least queues correctly,
- `tts stop` / `voice off` work.

Then clean up installer files:

```powershell
Remove-Item apply_0_0_8_spoken_response_pipeline_patch.py
Remove-Item -Recurse patch_files
```

Commit:

```powershell
git add .
git commit -m "0.0.8 Add spoken response pipeline"
git push
```
