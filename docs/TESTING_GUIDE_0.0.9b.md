# Testing Guide — 0.0.9b STT GPU Acceleration

## 1. Install/update STT requirements

From the Jarvis Ultimate root with the venv active:

```powershell
python -m pip install -r requirements-stt.txt
```

Optional helper:

```powershell
python -m pip install -r requirements-stt-gpu.txt
```

`requirements-stt-gpu.txt` covers Python-level helper packages. On Windows, CTranslate2 GPU may also require NVIDIA cuBLAS/cuDNN DLLs on PATH.

## 2. Confirm config

Run:

```powershell
python scripts/run_cli.py
```

Then:

```text
stt status
stt gpu status
```

Expected success indicators:

```text
requested device: auto
compute type: auto
CUDA detected for STT: True
```

It is okay if `CTranslate2 CUDA devices` is blank or zero at first, but if model load fails later, check `stt debug last`.

## 3. Warm the model

Run:

```text
stt warmup
```

Best success result:

```text
faster-whisper model warmed on cuda with float16.
```

Acceptable temporary result:

```text
CUDA warmup failed, but faster-whisper warmed on CPU fallback.
```

If it falls back to CPU, Jarvis will still work, but voice will not feel as responsive. Run `stt debug last` and check for missing CUDA/cuBLAS/cuDNN messages.

## 4. Test live mic transcription

Run:

```text
listen once
```

Say: `Hey Jarvis`.

Expected:

```text
Heard: Hey Jarvis
Provider: faster_whisper
```

Then run:

```text
stt debug last
```

Look for:

```text
device: cuda (float16)
elapsed_ms: ...
```

If you see:

```text
device: cpu (int8)
fallback_used: True
```

then GPU failed and CPU fallback was used.

## 5. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Expected:

```text
Ran 107 tests
OK
```

## 6. Commit only after manual checks pass

Cleanup:

```powershell
Remove-Item apply_0_0_9b_stt_gpu_acceleration_patch.py
Remove-Item -Recurse patch_files
```

Commit:

```powershell
git add .
git commit -m "0.0.9b Add GPU-aware STT acceleration"
git push
```
