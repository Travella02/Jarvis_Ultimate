"""CLI client for Jarvis 3."""

from __future__ import annotations

from jarvis.core.lifecycle import JarvisRuntime


EXIT_COMMANDS = {"exit", "quit", "q", "bye"}
TIMING_LAST_COMMANDS = {"timing last", "last timing", "show timing", "latency last"}
PROMPT_DIAGNOSTIC_COMMANDS = {"prompt stats", "prompt diagnostics", "llm prompt", "llm diagnostics"}
MEMORY_STATUS_COMMANDS = {"memory status", "short memory status", "short-term memory status", "stm status"}
MEMORY_LAST_COMMANDS = {"memory last", "memory recent", "short memory last", "short-term memory last", "stm last"}
MEMORY_CLEAR_COMMANDS = {"memory clear", "clear memory", "short memory clear", "short-term memory clear", "stm clear"}
STT_STATUS_COMMANDS = {"stt status", "mic status", "microphone status", "voice input status", "speech input status"}
STT_PROVIDERS_COMMANDS = {"stt providers", "mic providers", "speech input providers"}
STT_RECORD_COMMANDS = {"stt record", "mic record", "record mic", "record microphone"}
STT_LISTEN_ONCE_COMMANDS = {"listen once", "stt listen", "mic listen", "microphone listen", "stt test mic", "test microphone", "listen until done"}
STT_LISTEN_SETTINGS_COMMANDS = {"stt listen settings", "listen settings", "mic listen settings", "endpointing settings", "stt endpointing"}
STT_DEBUG_LAST_COMMANDS = {"stt debug last", "stt debug", "mic debug last", "speech input debug"}
VOICE_LOOP_STATUS_COMMANDS = {"voice loop status", "conversation loop status", "voice chat status", "talk status"}
VOICE_LOOP_ONCE_COMMANDS = {"voice loop once", "talk once", "voice chat once", "conversation once", "listen and respond", "listen respond", "respond once"}
WAKE_STATUS_COMMANDS = {"wake status", "wake word status", "wakeword status", "hey jarvis status"}
WAKE_LISTEN_ONCE_COMMANDS = {"wake listen once", "wake word listen", "listen for wake word", "wake test mic"}
WAKE_VOICE_ONCE_COMMANDS = {"wake voice once", "wake loop once", "wake respond once", "wake chat once", "hey jarvis once"}
STT_GPU_STATUS_COMMANDS = {"stt gpu", "stt gpu status", "stt cuda", "stt cuda status", "mic gpu status"}
STT_WARMUP_COMMANDS = {"stt warmup", "warm up stt", "stt load model", "load stt model", "mic warmup"}
TTS_WARMUP_COMMANDS = {"tts warmup", "warm up tts", "tts load model", "load tts model", "voice output warmup"}
WARMUP_STATUS_COMMANDS = {"warmup status", "warm up status", "voice warmup status", "readiness status"}
WARMUP_ALL_COMMANDS = {"warmup", "warmup all", "warm up", "warm up all", "voice warmup", "warm up jarvis", "ready jarvis"}
AUDIO_CLEANUP_COMMANDS = {"audio cleanup", "voice cleanup", "cleanup audio", "clean audio", "cleanup voice files"}
TTS_CLEANUP_COMMANDS = {"tts cleanup", "cleanup tts", "voice output cleanup"}
STT_CLEANUP_COMMANDS = {"stt cleanup", "mic cleanup", "microphone cleanup", "cleanup stt"}
LISTEN_PRESET_COMMANDS = {"listen faster", "listen fast", "listen balanced", "listen normal", "listen safer", "listen safe"}
TTS_STATUS_COMMANDS = {"tts status", "speech status"}
VOICE_STATUS_COMMANDS = {"voice status", "spoken status", "auto voice status"}
TTS_QUEUE_STATUS_COMMANDS = {"tts queue", "tts queue status", "voice queue", "voice queue status"}
TTS_STOP_COMMANDS = {"tts stop", "voice stop", "stop voice", "stop speaking", "silence"}
TTS_PROVIDERS_COMMANDS = {"tts providers", "voice providers", "tts provider"}
TTS_TEST_COMMANDS = {"tts test", "voice test", "test voice", "test tts"}
TTS_TEST_PLAY_COMMANDS = {"tts test play", "voice test play", "test voice play", "test tts play"}
TTS_PLAY_LAST_COMMANDS = {"tts play last", "voice play last", "play last voice", "play last tts"}
TTS_PLAYBACK_ON_COMMANDS = {"tts playback on", "playback on", "voice playback on", "tts sound on"}
TTS_PLAYBACK_OFF_COMMANDS = {"tts playback off", "playback off", "voice playback off", "tts sound off"}
TTS_REFERENCE_STATUS_COMMANDS = {"tts reference", "tts reference status", "xtts reference", "xtts reference status", "voice reference"}
TTS_DEBUG_LAST_COMMANDS = {"tts debug last", "tts last error", "tts debug", "voice debug last"}
TTS_XTTS_TEST_COMMANDS = {"tts xtts test", "xtts test", "test xtts"}  # experimental/personal-only
TTS_XTTS_TEST_PLAY_COMMANDS = {"tts xtts test play", "xtts test play", "test xtts play"}
TTS_VOICE_LIST_COMMANDS = {"tts voice list", "voice list", "tts voices", "kokoro voices", "tts kokoro voices", "xtts voice list"}
TTS_VOICE_CURRENT_COMMANDS = {"tts voice current", "voice current", "current voice", "tts current voice", "xtts voice current"}
VOICE_ON_COMMANDS = {"voice on", "tts on", "auto voice on", "auto speak on"}
VOICE_OFF_COMMANDS = {"voice off", "tts off", "auto voice off", "auto speak off"}
BENCHMARK_PREFIXES = {
    ("benchmark", "llm"),
    ("benchmark", "lm"),
    ("llm", "benchmark"),
    ("llm", "speed"),
    ("speed", "test"),
}
PROMPT_MODE_WORDS = {"normal", "minimal", "off", "none", "fast", "short"}
API_MODE_WORDS = {"openai", "native"}
REASONING_WORDS = {"auto", "default", "off", "low", "medium", "high", "on"}


def main() -> None:
    runtime = JarvisRuntime()
    boot_result = runtime.boot()
    print(boot_result.message)
    print(
        "Type 'exit' to stop Jarvis. Try: hello, status, list agents, screen check, "
        "timing last, prompt stats, memory status, memory last, stt status, stt listen settings, stt warmup, warmup all, listen faster, stt energy 0.03, listen once, wake status, wake voice once, voice loop once, talk once, voice on, voice stop, tts status, tts test play, tts voice list, tts voice use af_heart, benchmark llm"
    )

    while True:
        try:
            command = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            runtime.spoken_pipeline.shutdown()
            print("\nJarvis: Shutting down.")
            break

        normalized = command.lower()
        if normalized in EXIT_COMMANDS:
            runtime.spoken_pipeline.shutdown()
            print("Jarvis: Shutting down.")
            break

        if normalized in TIMING_LAST_COMMANDS:
            print(f"Jarvis: {runtime.timing_last()}")
            continue

        if normalized in PROMPT_DIAGNOSTIC_COMMANDS:
            print(f"Jarvis: {runtime.prompt_diagnostics()}")
            continue

        if normalized in MEMORY_STATUS_COMMANDS:
            print(f"Jarvis: {runtime.memory_status()}")
            continue

        memory_last_limit = _parse_memory_last_command(normalized)
        if memory_last_limit is not None:
            print(f"Jarvis: {runtime.memory_last(limit=memory_last_limit)}")
            continue

        if normalized in MEMORY_CLEAR_COMMANDS:
            print(f"Jarvis: {runtime.memory_clear()}")
            continue

        if normalized in STT_STATUS_COMMANDS:
            print(f"Jarvis: {runtime.stt_status()}")
            continue

        if normalized in STT_PROVIDERS_COMMANDS:
            print(f"Jarvis: {runtime.stt_providers()}")
            continue

        if normalized in STT_GPU_STATUS_COMMANDS:
            print(f"Jarvis: {runtime.stt_gpu_status()}")
            continue

        if normalized in STT_WARMUP_COMMANDS:
            print("Jarvis: Warming STT model...")
            print(f"Jarvis: {runtime.stt_warmup()}")
            continue

        if normalized in TTS_WARMUP_COMMANDS:
            print("Jarvis: Warming TTS provider...")
            print(f"Jarvis: {runtime.tts_warmup()}")
            continue

        if normalized in WARMUP_STATUS_COMMANDS:
            print(f"Jarvis: {runtime.warmup_status()}")
            continue

        if normalized in WARMUP_ALL_COMMANDS:
            print("Jarvis: Warming voice systems...")
            print(f"Jarvis: {runtime.warmup_all()}")
            continue

        if normalized in AUDIO_CLEANUP_COMMANDS:
            print(f"Jarvis: {runtime.audio_cleanup()}")
            continue

        if normalized in TTS_CLEANUP_COMMANDS:
            print(f"Jarvis: {runtime.tts_cleanup()}")
            continue

        if normalized in STT_CLEANUP_COMMANDS:
            print(f"Jarvis: {runtime.stt_cleanup()}")
            continue

        listen_preset = _parse_listen_preset_command(normalized)
        if listen_preset is not None:
            print(f"Jarvis: {runtime.stt_set_latency_preset(listen_preset)}")
            continue

        silence_override = _parse_stt_silence_set_command(command)
        if silence_override is not None:
            print(f"Jarvis: {runtime.stt_set_silence_seconds(silence_override)}")
            continue

        energy_override = _parse_stt_energy_set_command(command)
        if energy_override is not None:
            print(f"Jarvis: {runtime.stt_set_energy_threshold(energy_override)}")
            continue

        adaptive_override = _parse_stt_adaptive_energy_command(normalized)
        if adaptive_override is not None:
            print(f"Jarvis: {runtime.stt_set_adaptive_energy(adaptive_override)}")
            continue

        if normalized in STT_LISTEN_SETTINGS_COMMANDS:
            print(f"Jarvis: {runtime.stt_listen_settings()}")
            continue

        if normalized in STT_RECORD_COMMANDS:
            print("Jarvis: Recording a short microphone clip...")
            print(f"Jarvis: {runtime.stt_record()}")
            continue

        listen_options = _parse_stt_listen_command(command)
        if listen_options is not None:
            mode_label = listen_options.get("mode") or "configured"
            print(f"Jarvis: Listening once ({mode_label})...")
            output = runtime.stt_listen_once(
                duration_seconds=listen_options.get("duration_seconds"),
                mode=listen_options.get("mode"),
                silence_seconds=listen_options.get("silence_seconds"),
            )
            print(f"Jarvis: {output}")
            continue

        if normalized in STT_DEBUG_LAST_COMMANDS:
            print(f"Jarvis: {runtime.stt_debug_last()}")
            continue

        if normalized in WAKE_STATUS_COMMANDS:
            print(f"Jarvis: {runtime.wake_status()}")
            continue

        wake_test_text = _parse_wake_test_command(command)
        if wake_test_text is not None:
            print(f"Jarvis: {runtime.wake_test(wake_test_text)}")
            continue

        wake_listen_options = _parse_wake_listen_command(command)
        if wake_listen_options is not None:
            mode_label = wake_listen_options.get("mode") or "configured"
            print(f"Jarvis: Listening for wake word ({mode_label})...")
            print(f"Jarvis: {runtime.wake_listen_once(duration_seconds=wake_listen_options.get('duration_seconds'), mode=wake_listen_options.get('mode'), silence_seconds=wake_listen_options.get('silence_seconds'))}")
            continue

        wake_voice_options = _parse_wake_voice_command(command)
        if wake_voice_options is not None:
            mode_label = wake_voice_options.get("mode") or "configured"
            print(f"Jarvis: Listening for wake word and command ({mode_label})...")
            state = {"started": False}

            def print_wake_stream_chunk(chunk: str) -> None:
                if not state["started"]:
                    print("Jarvis: ", end="", flush=True)
                    state["started"] = True
                print(chunk, end="", flush=True)

            def print_wake_transcript(transcript: str) -> None:
                print(f"Heard: {transcript}")

            result = runtime.wake_voice_once(
                duration_seconds=wake_voice_options.get("duration_seconds"),
                mode=wake_voice_options.get("mode"),
                silence_seconds=wake_voice_options.get("silence_seconds"),
                stream_callback=print_wake_stream_chunk,
                transcript_callback=print_wake_transcript,
                speak=True,
            )
            if state["started"]:
                print()
                if not result.success:
                    print(f"Jarvis: {result.message}")
            else:
                print(f"Jarvis: {result.message}")
            continue

        if normalized in VOICE_LOOP_STATUS_COMMANDS:
            print(f"Jarvis: {runtime.voice_loop_status()}")
            continue

        voice_loop_options = _parse_voice_loop_command(command)
        if voice_loop_options is not None:
            mode_label = voice_loop_options.get("mode") or "configured"
            print(f"Jarvis: Listening for one voice turn ({mode_label})...")
            state = {"started": False}

            def print_voice_stream_chunk(chunk: str) -> None:
                if not state["started"]:
                    print("Jarvis: ", end="", flush=True)
                    state["started"] = True
                print(chunk, end="", flush=True)

            def print_transcript(transcript: str) -> None:
                print(f"Heard: {transcript}")

            result = runtime.voice_loop_once(
                duration_seconds=voice_loop_options.get("duration_seconds"),
                mode=voice_loop_options.get("mode"),
                silence_seconds=voice_loop_options.get("silence_seconds"),
                stream_callback=print_voice_stream_chunk,
                transcript_callback=print_transcript,
                speak=True,
            )
            if state["started"]:
                print()
                if not result.success:
                    print(f"Jarvis: {result.message}")
            else:
                print(f"Jarvis: {result.message}")
            continue

        stt_file_path = _parse_stt_transcribe_command(command)
        if stt_file_path is not None:
            print(f"Jarvis: {runtime.stt_transcribe_file(stt_file_path)}")
            continue

        if normalized in VOICE_STATUS_COMMANDS:
            print(f"Jarvis: {runtime.voice_status()}")
            continue

        if normalized in TTS_QUEUE_STATUS_COMMANDS:
            print(f"Jarvis: {runtime.tts_queue_status()}")
            continue

        if normalized in TTS_STOP_COMMANDS:
            print(f"Jarvis: {runtime.tts_stop()}")
            continue

        if normalized in TTS_STATUS_COMMANDS:
            print(f"Jarvis: {runtime.tts_status()}")
            continue

        if normalized in TTS_PROVIDERS_COMMANDS:
            print(f"Jarvis: {runtime.tts_providers()}")
            continue

        if normalized in TTS_TEST_PLAY_COMMANDS:
            print(f"Jarvis: {runtime.tts_test(play_audio=True)}")
            continue

        if normalized in TTS_TEST_COMMANDS:
            print(f"Jarvis: {runtime.tts_test()}")
            continue

        if normalized in TTS_PLAY_LAST_COMMANDS:
            print(f"Jarvis: {runtime.tts_play_last()}")
            continue

        if normalized in TTS_PLAYBACK_ON_COMMANDS:
            print(f"Jarvis: {runtime.tts_playback_on()}")
            continue

        if normalized in TTS_PLAYBACK_OFF_COMMANDS:
            print(f"Jarvis: {runtime.tts_playback_off()}")
            continue

        if normalized in TTS_REFERENCE_STATUS_COMMANDS:
            print(f"Jarvis: {runtime.tts_reference_status()}")
            continue

        if normalized in TTS_DEBUG_LAST_COMMANDS:
            print(f"Jarvis: {runtime.tts_debug_last()}")
            continue

        if normalized in TTS_XTTS_TEST_PLAY_COMMANDS:
            print(f"Jarvis: {runtime.tts_xtts_test(play_audio=True)}")
            continue

        if normalized in TTS_XTTS_TEST_COMMANDS:
            print(f"Jarvis: {runtime.tts_xtts_test()}")
            continue

        if normalized in TTS_VOICE_LIST_COMMANDS:
            print(f"Jarvis: {runtime.tts_voice_list()}")
            continue

        if normalized in TTS_VOICE_CURRENT_COMMANDS:
            print(f"Jarvis: {runtime.tts_voice_current()}")
            continue

        voice_import_options = _parse_tts_voice_import_command(command)
        if voice_import_options is not None:
            print(f"Jarvis: {runtime.tts_voice_import(voice_import_options['voice_name'], voice_import_options['path'], activate=voice_import_options['activate'])}")
            continue

        voice_use_name = _parse_tts_voice_use_command(command)
        if voice_use_name is not None:
            print(f"Jarvis: {runtime.tts_voice_use(voice_use_name)}")
            continue

        voice_delete_name = _parse_tts_voice_delete_command(command)
        if voice_delete_name is not None:
            print(f"Jarvis: {runtime.tts_voice_delete(voice_delete_name)}")
            continue

        voice_test_options = _parse_tts_voice_test_command(command)
        if voice_test_options is not None:
            print(f"Jarvis: {runtime.tts_voice_test(voice_test_options['voice_name'], play_audio=voice_test_options['play_audio'])}")
            continue

        say_as_options = _parse_tts_say_as_command(command)
        if say_as_options is not None:
            print(f"Jarvis: {runtime.tts_say_as(say_as_options['voice_name'], say_as_options['text'], play_audio=say_as_options['play_audio'])}")
            continue

        reference_options = _parse_tts_reference_command(command)
        if reference_options is not None:
            print(f"Jarvis: {runtime.tts_reference_set(reference_options['path'], import_to_default=reference_options['import_to_default'])}")
            continue

        tts_text = _parse_tts_say_command(command)
        if tts_text is not None:
            print(f"Jarvis: {runtime.tts_say(tts_text)}")
            continue

        if normalized in VOICE_ON_COMMANDS:
            print(f"Jarvis: {runtime.voice_on()}")
            continue

        if normalized in VOICE_OFF_COMMANDS:
            print(f"Jarvis: {runtime.voice_off()}")
            continue

        benchmark_options = _parse_benchmark_command(normalized)
        if benchmark_options is not None:
            print("Jarvis: Running direct LLM benchmark...")
            print(f"Jarvis: {runtime.benchmark_llm(**benchmark_options)}")
            continue

        state = {"started": False}

        def print_stream_chunk(chunk: str) -> None:
            if not state["started"]:
                print("Jarvis: ", end="", flush=True)
                state["started"] = True
            print(chunk, end="", flush=True)

        spoken_stream = runtime.create_spoken_stream(print_stream_chunk) if runtime.tts_manager.auto_speak else None
        callback = spoken_stream if spoken_stream is not None else print_stream_chunk
        result = runtime.handle_command(command, stream_callback=callback)
        if spoken_stream is not None:
            speak_remaining = bool(result.success and result.action == "llm_chat")
            spoken_stream.finish(speak_remaining=speak_remaining)
        if state["started"]:
            print()
            if not result.success:
                print(f"Jarvis: {result.message}")
        else:
            print(f"Jarvis: {result.message}")




def _parse_listen_preset_command(normalized: str) -> str | None:
    if normalized in {"listen faster", "listen fast"}:
        return "faster"
    if normalized in {"listen balanced", "listen normal"}:
        return "balanced"
    if normalized in {"listen safer", "listen safe"}:
        return "safer"
    return None


def _parse_stt_silence_set_command(command: str) -> float | None:
    stripped = command.strip()
    lowered = stripped.lower()
    prefixes = ("stt silence ", "listen silence ", "silence stop ", "set silence ")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            value = stripped[len(prefix):].strip().lower().replace("seconds", "").replace("second", "").strip()
            try:
                return float(value)
            except ValueError:
                return None
    return None


def _parse_stt_energy_set_command(command: str) -> float | None:
    stripped = command.strip()
    lowered = stripped.lower()
    prefixes = ("stt energy ", "listen energy ", "mic energy ", "energy threshold ", "set energy ")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            value = stripped[len(prefix):].strip().lower().replace("threshold", "").strip()
            try:
                return float(value)
            except ValueError:
                return None
    return None


def _parse_stt_adaptive_energy_command(normalized: str) -> bool | None:
    if normalized in {"stt adaptive on", "stt adaptive energy on", "listen adaptive on", "adaptive energy on"}:
        return True
    if normalized in {"stt adaptive off", "stt adaptive energy off", "listen adaptive off", "adaptive energy off"}:
        return False
    return None



def _strip_quotes(value: str) -> str:
    return value.strip().strip('"').strip("'")


def _parse_tts_voice_import_command(command: str) -> dict[str, object] | None:
    """Parse commands like 'tts voice import jarvis C:\\voice.wav'."""
    stripped = command.strip()
    lowered = stripped.lower()
    prefixes = (
        "tts voice import ",
        "tts voice create ",
        "xtts voice import ",
        "xtts voice create ",
        "voice import ",
    )
    for prefix in prefixes:
        if lowered.startswith(prefix):
            rest = stripped[len(prefix):].strip()
            parts = rest.split(maxsplit=1)
            if len(parts) != 2:
                return None
            return {"voice_name": _strip_quotes(parts[0]), "path": _strip_quotes(parts[1]), "activate": True}
    return None


def _parse_tts_voice_use_command(command: str) -> str | None:
    stripped = command.strip()
    lowered = stripped.lower()
    prefixes = ("tts voice use ", "tts voice set ", "voice use ", "kokoro voice use ", "tts kokoro voice use ", "xtts voice use ")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return _strip_quotes(stripped[len(prefix):].strip()) or None
    return None


def _parse_tts_voice_delete_command(command: str) -> str | None:
    stripped = command.strip()
    lowered = stripped.lower()
    prefixes = ("tts voice delete ", "tts voice remove ", "voice delete ", "xtts voice delete ")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return _strip_quotes(stripped[len(prefix):].strip()) or None
    return None


def _parse_tts_voice_test_command(command: str) -> dict[str, object] | None:
    stripped = command.strip()
    lowered = stripped.lower()
    prefixes = ("tts voice test ", "voice test ", "kokoro voice test ", "tts kokoro voice test ", "xtts voice test ")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            rest = stripped[len(prefix):].strip()
            play_audio = False
            if rest.lower().endswith(" play"):
                play_audio = True
                rest = rest[:-5].strip()
            return {"voice_name": _strip_quotes(rest) or None, "play_audio": play_audio}
    return None


def _parse_tts_say_as_command(command: str) -> dict[str, object] | None:
    """Parse commands like 'tts say as jarvis Hello sir'."""
    stripped = command.strip()
    lowered = stripped.lower()
    prefixes = ("tts say as ", "voice say as ", "speak as ")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            rest = stripped[len(prefix):].strip()
            parts = rest.split(maxsplit=1)
            if len(parts) != 2:
                return None
            return {"voice_name": _strip_quotes(parts[0]), "text": parts[1].strip(), "play_audio": None}
    return None

def _parse_tts_say_command(command: str) -> str | None:
    """Parse commands like 'tts say hello' without lowercasing the text."""
    stripped = command.strip()
    lowered = stripped.lower()
    prefixes = ("tts say ", "say aloud ", "voice say ", "speak ")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return stripped[len(prefix):].strip()
    return None


def _parse_tts_reference_command(command: str) -> dict[str, object] | None:
    """Parse XTTS reference setup commands while preserving Windows paths."""
    stripped = command.strip()
    lowered = stripped.lower()
    import_prefixes = ("tts reference import ", "xtts reference import ", "voice reference import ")
    set_prefixes = ("tts reference set ", "xtts reference set ", "voice reference set ")
    for prefix in import_prefixes:
        if lowered.startswith(prefix):
            return {"path": stripped[len(prefix):].strip().strip('"'), "import_to_default": True}
    for prefix in set_prefixes:
        if lowered.startswith(prefix):
            return {"path": stripped[len(prefix):].strip().strip('"'), "import_to_default": False}
    return None



def _parse_wake_test_command(command: str) -> str | None:
    """Parse typed wake-word checks, preserving the text being tested."""
    stripped = command.strip()
    lowered = stripped.lower()
    prefixes = ("wake test ", "wake word test ", "test wake ", "test wake word ")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return stripped[len(prefix):].strip() or None
    return None


def _parse_wake_listen_command(command: str) -> dict[str, float | str | None] | None:
    """Parse one-turn wake-listen commands without routing to the LLM."""
    stripped = command.strip()
    lowered = stripped.lower()
    if lowered in WAKE_LISTEN_ONCE_COMMANDS:
        return {"mode": None, "duration_seconds": None, "silence_seconds": None}
    prefixes = ("wake listen ", "wake word listen ", "listen wake ")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            listen_like = "listen " + stripped[len(prefix):].strip()
            parsed = _parse_stt_listen_command(listen_like)
            if parsed is not None:
                return parsed
            if stripped[len(prefix):].strip().lower() in {"once", "now"}:
                return {"mode": None, "duration_seconds": None, "silence_seconds": None}
    return None


def _parse_wake_voice_command(command: str) -> dict[str, float | str | None] | None:
    """Parse one-turn wake phrase -> command -> spoken response commands."""
    stripped = command.strip()
    lowered = stripped.lower()
    if lowered in WAKE_VOICE_ONCE_COMMANDS:
        return {"mode": None, "duration_seconds": None, "silence_seconds": None}
    prefixes = ("wake voice ", "wake loop ", "wake chat ", "wake respond ", "hey jarvis ")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            rest = stripped[len(prefix):].strip()
            if rest.lower() in {"once", "now", ""}:
                return {"mode": None, "duration_seconds": None, "silence_seconds": None}
            listen_like = "listen " + rest
            parsed = _parse_stt_listen_command(listen_like)
            if parsed is not None:
                return parsed
    return None


def _parse_voice_loop_command(command: str) -> dict[str, float | str | None] | None:
    """Parse commands for one full spoken turn.

    Supported examples:
    - voice loop once
    - talk once
    - listen and respond
    - voice loop smart max 8 silence 0.8
    - voice loop fixed 2
    """
    stripped = command.strip()
    lowered = stripped.lower()
    if lowered in VOICE_LOOP_ONCE_COMMANDS:
        return {"mode": None, "duration_seconds": None, "silence_seconds": None}

    prefixes = ("voice loop ", "voice chat ", "conversation ", "talk ")
    selected_prefix = None
    for prefix in prefixes:
        if lowered.startswith(prefix):
            selected_prefix = prefix
            break
    if selected_prefix is None:
        return None

    listen_like = "listen " + stripped[len(selected_prefix):].strip()
    parsed = _parse_stt_listen_command(listen_like)
    if parsed is None and stripped[len(selected_prefix):].strip().lower() in {"once", "now"}:
        return {"mode": None, "duration_seconds": None, "silence_seconds": None}
    return parsed


def _parse_stt_listen_command(command: str) -> dict[str, float | str | None] | None:
    """Parse low-latency listen commands.

    Supported examples:
    - listen once
    - listen smart
    - listen smart max 6 silence 0.8
    - listen fixed 2
    - listen 2              # duration override using configured listen mode
    """
    stripped = command.strip()
    lowered = stripped.lower()
    if lowered in STT_LISTEN_ONCE_COMMANDS:
        return {"mode": None, "duration_seconds": None, "silence_seconds": None}

    words = lowered.split()
    if not words:
        return None
    if words[0] == "stt" and len(words) >= 2 and words[1] == "listen":
        words = words[1:]
    if not words or words[0] != "listen":
        return None

    mode: str | None = None
    duration_seconds: float | None = None
    silence_seconds: float | None = None
    recognized = False
    index = 1
    if index < len(words) and words[index] in {"once", "smart", "fixed"}:
        recognized = True
        if words[index] in {"smart", "fixed"}:
            mode = words[index]
        index += 1

    while index < len(words):
        token = words[index]
        if token in {"max", "duration", "for", "seconds"} and index + 1 < len(words):
            duration_seconds = _parse_positive_float(words[index + 1])
            recognized = recognized or duration_seconds is not None
            index += 2
            continue
        if token in {"silence", "pause", "quiet"} and index + 1 < len(words):
            silence_seconds = _parse_positive_float(words[index + 1])
            recognized = recognized or silence_seconds is not None
            index += 2
            continue
        number = _parse_positive_float(token)
        if number is not None and duration_seconds is None:
            duration_seconds = number
            recognized = True
        index += 1

    if not recognized:
        return None
    return {"mode": mode, "duration_seconds": duration_seconds, "silence_seconds": silence_seconds}


def _parse_positive_float(value: str) -> float | None:
    try:
        number = float(value)
    except ValueError:
        return None
    return number if number > 0 else None


def _parse_stt_transcribe_command(command: str) -> str | None:
    """Parse commands like 'stt transcribe C:\\path\\clip.wav'."""
    stripped = command.strip()
    lowered = stripped.lower()
    prefixes = ("stt transcribe file ", "stt transcribe ", "transcribe audio ", "transcribe file ")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return stripped[len(prefix):].strip().strip('"') or None
    return None


def _parse_memory_last_command(normalized_command: str) -> int | None:
    """Parse memory-last commands with optional numeric limits."""
    if normalized_command in MEMORY_LAST_COMMANDS:
        return 5
    words = normalized_command.split()
    if len(words) == 3 and words[0] == "memory" and words[1] == "last":
        try:
            return max(1, min(20, int(words[2])))
        except ValueError:
            return 5
    return None


def _parse_benchmark_command(normalized_command: str) -> dict[str, str | None] | None:
    """Parse direct benchmark commands.

    Supported examples:
    - benchmark llm
    - benchmark llm minimal
    - benchmark llm off        # old behavior: prompt mode off
    - benchmark lm openai
    - benchmark lm native
    - benchmark lm native off  # native API, reasoning/thinking off
    - benchmark lm native low
    """
    words = normalized_command.split()
    if len(words) < 2:
        return None
    if tuple(words[:2]) not in BENCHMARK_PREFIXES:
        return None

    tokens = words[2:]
    api_mode_present = any(token in API_MODE_WORDS for token in tokens)
    options: dict[str, str | None] = {"prompt_mode": None, "api_mode": None, "reasoning": None}

    for token in tokens:
        if token in API_MODE_WORDS:
            options["api_mode"] = token
        elif token in REASONING_WORDS and api_mode_present:
            options["reasoning"] = "auto" if token == "default" else token
        elif token in PROMPT_MODE_WORDS:
            options["prompt_mode"] = token

    return options


if __name__ == "__main__":
    main()
