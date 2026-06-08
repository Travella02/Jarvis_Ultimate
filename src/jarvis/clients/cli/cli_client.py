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
        "timing last, prompt stats, memory status, memory last, tts status, tts test, benchmark llm"
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

        if normalized in TTS_TEST_COMMANDS:
            print(f"Jarvis: {runtime.tts_test()}")
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
            print(f"Jarvis voice: {runtime.tts_say(result.message)}")



def _parse_tts_say_command(command: str) -> str | None:
    """Parse commands like 'tts say hello' without lowercasing the text."""
    stripped = command.strip()
    lowered = stripped.lower()
    prefixes = ("tts say ", "say aloud ", "voice say ", "speak ")
    for prefix in prefixes:
        if lowered.startswith(prefix):
            return stripped[len(prefix):].strip()
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
