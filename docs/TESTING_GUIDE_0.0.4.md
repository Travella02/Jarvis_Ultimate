# Testing Guide — Jarvis Ultimate 0.0.4

## Goal

Confirm that Jarvis still boots, routes normal conversation through LM Studio, and can show timing diagnostics for the last command.

## 1. Apply the patch

From the extracted patch package, copy these into the Jarvis Ultimate root folder:

```text
apply_0_0_4_latency_fast_path_patch.py
patch_files/
```

Your Jarvis root is usually:

```text
C:\Users\tanne\OneDrive\Desktop\Jarvis Ultimate
```

Then open PowerShell in the Jarvis root and run:

```powershell
python apply_0_0_4_latency_fast_path_patch.py
```

## 2. Activate your venv

```powershell
.venv\Scripts\activate
```

## 3. Run the boot smoke test

```powershell
python scripts/run_jarvis.py
```

Success should look like Jarvis booting and reporting the registered agents. This command should not need LM Studio for the basic boot check.

## 4. Run the CLI

Make sure LM Studio is open, a model is loaded, and the Local Server is running at:

```text
http://localhost:1234/v1
```

Then run:

```powershell
python scripts/run_cli.py
```

Try a normal message:

```text
hello Jarvis, can you hear me?
```

Then run:

```text
timing last
```

## 5. What success looks like

The timing output should include lines similar to:

```text
lm_studio.model_resolved ... mode=fast_path
lm_studio.request_start ... path=/chat/completions
lm_studio.request_finished ... path=/chat/completions
Pre-LM Studio request time: ... ms
LM Studio request/response time: ... ms
```

The important part is that `lm_studio.request_start` appears quickly. If the big delay is before that line, Jarvis is still spending time before the request. If the big delay is after that line, LM Studio/model response time is the bottleneck.

## 6. Run the full test suite

From the Jarvis root:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 26 tests
OK
```

## 7. Clean up installer files after success

After the tests and manual CLI timing check pass, you can delete:

```text
apply_0_0_4_latency_fast_path_patch.py
patch_files/
```

## 8. Commit only after tests/manual checks pass

```powershell
git add .
git commit -m "0.0.4 Add LM Studio latency diagnostics and fast path"
git push
```

## Common issues

### LM Studio connection error

Jarvis will say it could not connect to LM Studio. Open LM Studio, load a model, enable the Local Server, then try again.

### `timing last` says no timing recorded

Send a normal Jarvis message first. `timing last` reports the previous command, and the timing command itself does not replace the previous timing data.

### LM Studio rejects `local-model`

Most LM Studio local-server setups accept the placeholder model name, but if yours rejects it, open `config/providers.yaml` and replace:

```yaml
model: auto
```

with the exact model id shown in LM Studio, or set:

```yaml
resolve_auto_model: true
```

That will restore the `/v1/models` lookup only when needed.
