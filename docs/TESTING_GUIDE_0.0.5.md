# Testing Guide — Jarvis Ultimate 0.0.5

## Goal

Confirm that Jarvis still boots, the CLI still works, LM Studio conversation now streams visibly, and `timing last` shows time-to-first streamed chunk.

## 1. Apply the patch

From the extracted patch package, copy these into the Jarvis Ultimate root folder:

```text
apply_0_0_5_streaming_lm_studio_patch.py
patch_files/
```

Your Jarvis root is usually:

```text
C:\Users\tanne\OneDrive\Desktop\Jarvis Ultimate
```

Then open PowerShell in the Jarvis root and run:

```powershell
python apply_0_0_5_streaming_lm_studio_patch.py
```

## 2. Activate your venv

```powershell
.venv\Scripts\activate
```

## 3. Run the boot smoke test

```powershell
python scripts/run_jarvis.py
```

Success should look like:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 4. Run the full test suite

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 30 tests
OK
```

## 5. Manual CLI streaming check

Make sure LM Studio is open, a model is loaded, and the Local Server is running at:

```text
http://localhost:1234/v1
```

Then run:

```powershell
python scripts/run_cli.py
```

Send a normal message, for example:

```text
hey Jarvis, explain what changed in this update
```

## 6. What success looks like

In 0.0.5, Jarvis should start printing the answer in the CLI as chunks arrive instead of waiting silently for the whole response.

Then run:

```text
timing last
```

Good timing output should include lines similar to:

```text
lm_studio.request_start ... path=/chat/completions, stream=True
lm_studio.stream_opened ...
lm_studio.first_chunk ...
lm_studio.request_finished ... stream=True
LM Studio time to first streamed chunk: ... ms
LM Studio remaining stream time: ... ms
LM Studio request/response time: ... ms
```

The most important number is `LM Studio time to first streamed chunk`. That is what affects how fast Jarvis feels in real conversation.

## 7. Check normal commands still work

Inside the CLI, try:

```text
status
list agents
screen check
timing last
```

Success means:

- `status` reports Jarvis is online and shows streaming enabled.
- `list agents` lists the registered agents.
- `screen check` routes to the Screen Agent placeholder.
- `timing last` still reports the previous command timing.

## 8. Temporarily disable streaming if needed

If LM Studio rejects streaming for your current model/server setup, open:

```text
config/providers.yaml
```

Change:

```yaml
streaming: true
```

to:

```yaml
streaming: false
```

Then rerun:

```powershell
python scripts/run_cli.py
```

That returns Jarvis to full-response mode without removing the 0.0.5 code.

## 9. Clean up installer files after success

After the tests and manual streaming check pass, you can delete:

```text
apply_0_0_5_streaming_lm_studio_patch.py
patch_files/
```

## 10. Commit only after tests/manual checks pass

```powershell
git add .
git commit -m "0.0.5 Add streaming LM Studio responses"
git push
```

## Common issues

### Nothing streams, but the full answer eventually appears

Check `config/providers.yaml` and make sure this is set:

```yaml
streaming: true
```

Also run `timing last` and look for `stream=True` on `lm_studio.request_start`.

### LM Studio connection error

Open LM Studio, load a model, enable the Local Server, then try again.

### LM Studio rejects `local-model`

If your LM Studio setup requires an exact model id, open `config/providers.yaml` and replace:

```yaml
model: auto
```

with the exact model id shown in LM Studio, or set:

```yaml
resolve_auto_model: true
```

### Streaming looks choppy

That usually means the model is generating small token chunks. It is still better than waiting silently for the whole response. Future UI/avatar work can smooth this visually.
