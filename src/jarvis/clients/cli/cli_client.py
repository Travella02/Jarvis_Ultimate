"""CLI client for Jarvis 3."""

from __future__ import annotations

from jarvis.core.lifecycle import JarvisRuntime


EXIT_COMMANDS = {"exit", "quit", "q", "bye"}
TIMING_LAST_COMMANDS = {"timing last", "last timing", "show timing", "latency last"}
PROMPT_DIAGNOSTIC_COMMANDS = {"prompt stats", "prompt diagnostics", "llm prompt", "llm diagnostics"}
MEMORY_STATUS_COMMANDS = {"memory status", "short memory status", "short-term memory status", "stm status"}
MEMORY_LAST_COMMANDS = {"memory last", "memory recent", "short memory last", "short-term memory last", "stm last"}
MEMORY_CLEAR_COMMANDS = {"memory clear", "clear memory", "short memory clear", "short-term memory clear", "stm clear"}
TTS_STATUS_COMMANDS = {"tts status", "voice status", "speech status"}
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
        "timing last, prompt stats, memory status, memory last, tts status, tts test, tts test play, tts voice list, tts voice use af_heart, benchmark llm"
    )

    while True:
        try:
            command = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nJarvis: Shutting down.")
            break

        normalized = command.lower()
        if normalized in EXIT_COMMANDS:
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

        result = runtime.handle_command(command, stream_callback=print_stream_chunk)
        if state["started"]:
            print()
            if not result.success:
                print(f"Jarvis: {result.message}")
        else:
            print(f"Jarvis: {result.message}")

        if runtime.tts_manager.auto_speak and result.success and result.message:
            print(f"Jarvis voice: {runtime.tts_say(result.message, play_audio=True)}")




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
