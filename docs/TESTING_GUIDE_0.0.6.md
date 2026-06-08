# Testing Guide — 0.0.6 Short-Term Conversation Memory

## Goal

Verify that Jarvis keeps a bounded short-term conversation window, uses it for follow-up LLM chat, and exposes simple memory diagnostics from the CLI.

## 1. Apply the patch

From the extracted patch package, copy these into your Jarvis Ultimate root:

```text
apply_0_0_6_short_term_memory_patch.py
patch_files/
```

Your project root should be similar to:

```text
C:\Users\tanne\Desktop\Jarvis_Ultimate
```

Run:

```powershell
python apply_0_0_6_short_term_memory_patch.py
```

Expected result:

```text
Patch installed.
```

## 2. Run the automated tests

Run:

```powershell
python -m unittest discover -s tests -v
```

Expected result:

```text
Ran 63 tests
OK
```

The exact runtime in seconds can be different.

## 3. Boot check

Run:

```powershell
python scripts/run_jarvis.py
```

Expected result:

```text
Jarvis 3 is online. Registered 9 agents.
```

## 4. CLI memory command check

Run:

```powershell
python scripts/run_cli.py
```

Then run:

```text
memory status
```

Expected result should include:

```text
Short-term memory status:
- enabled: True
- stored turns: 0 / 20
- injected turns per LLM chat: 8
```

Then run:

```text
memory last
```

Expected result before chatting:

```text
Short-term memory is empty.
```

## 5. Manual conversation memory check

With LM Studio running, say something simple that requires follow-up context:

```text
My test code word is blue comet.
```

Then run:

```text
memory status
```

Expected result should show at least:

```text
stored turns: 1 / 20
```

Then run:

```text
memory last
```

Expected result should show your recent user message and Jarvis's answer.

Now ask:

```text
What is my test code word?
```

Expected result:

Jarvis should be able to use the recent conversation context and answer with something close to:

```text
blue comet
```

Because this uses the local LLM, wording may vary.

## 6. Timing check

After a normal message, run:

```text
timing last
```

Expected timing output should include:

```text
conversation.memory_context_selected
memory.short_term_turn_saved
```

`conversation.memory_context_selected` shows how many recent turns were injected into the LLM request.

## 7. Clear memory check

Run:

```text
memory clear
```

Expected result:

```text
Short-term memory cleared. Removed X turn(s).
```

Then run:

```text
memory last
```

Expected result:

```text
Short-term memory is empty.
```

## 8. Config check

The patch adds these settings to `.env.example`:

```env
JARVIS_MEMORY_SHORT_TERM_ENABLED=true
JARVIS_MEMORY_SHORT_TERM_MAX_TURNS=20
JARVIS_MEMORY_SHORT_TERM_MAX_CHARS=12000
JARVIS_MEMORY_SHORT_TERM_INJECT_LAST_TURNS=8
JARVIS_MEMORY_SHORT_TERM_AUTOSAVE=false
```

For now, leave autosave false unless you specifically want Jarvis to restore recent session memory after restart.

## 9. Cleanup after successful test

After tests and manual checks pass, remove the temporary installer files:

```powershell
Remove-Item apply_0_0_6_short_term_memory_patch.py
Remove-Item -Recurse patch_files
```

## 10. Commit only after success

Only commit after:

- automated tests pass
- boot check passes
- CLI opens
- `memory status` works
- `memory last` works
- a follow-up question can use recent context
- `memory clear` works

Recommended commit:

```powershell
git add .
git commit -m "0.0.6 Add short-term conversation memory"
git push
```

## Common issues

### Jarvis does not remember the follow-up

Check:

```text
memory status
memory last
timing last
```

If `memory last` is empty, the first message may have routed to a placeholder agent instead of normal chat. Try a normal conversational sentence that does not include words like `remember`, `file`, `screen`, or `record`.

### Jarvis gets slower after many messages

Lower these settings in `.env`:

```env
JARVIS_MEMORY_SHORT_TERM_INJECT_LAST_TURNS=4
JARVIS_MEMORY_SHORT_TERM_MAX_TURNS=12
```

### Memory resets after restart

That is expected by default. Short-term autosave is off:

```env
JARVIS_MEMORY_SHORT_TERM_AUTOSAVE=false
```

Turn it on only if you want recent session memory restored after restarts.
