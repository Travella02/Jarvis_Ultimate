# Jarvis Ultimate 0.3.3 Testing Guide

## 1. Apply the patch

From the Jarvis project root, run:

```powershell
python apply_0_3_3_typed_input_voice_parity_patch.py
```

## 2. Run the automated tests

```powershell
python -m unittest discover -s tests -v
```

If imports fail in a fresh PowerShell window, run:

```powershell
$env:PYTHONPATH="src"
python -m unittest discover -s tests -v
```

## 3. Start Jarvis

```powershell
python scripts\start_jarvis_app.py
```

Or double-click:

```powershell
Start_Jarvis_Ultimate_App.bat
```

## 4. Manual typed-input voice parity test

Let the app shell finish warming voice systems and start sleep/wake mode. Then type a command into the interface, without saying the wake word:

```text
Who is Kenleigh?
```

Expected result:

- Jarvis routes the typed command normally.
- Jarvis answers out loud through TTS.
- The orb caption shows the answer while/after Jarvis speaks.
- Jarvis does not require `Hey Jarvis` for the typed command.
- Jarvis does not stop the voice sleep/wake loop afterward.

## 5. Manual voice-after-typing test

After the typed response finishes, speak a normal wake command:

```text
Hey Jarvis, what do you remember about Kenleigh?
```

Expected result:

- Jarvis should still hear the wake phrase.
- Jarvis should answer normally.
- The UI should not be stuck in idle or silent typed-only mode.

## 6. Manual tool-response test

Type a non-memory/tool command such as:

```text
Open calculator.
```

Expected result:

- Jarvis should say the result out loud if TTS is enabled.
- Short tool responses should appear under the orb before or while Jarvis speaks, not only after speech finishes.

## 7. Success criteria

This patch is successful when typed commands and spoken commands feel like the same Jarvis interaction path, except typed commands do not need a wake word.
