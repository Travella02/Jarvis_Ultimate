"""CLI client for Jarvis 3."""

from __future__ import annotations

from jarvis.core.lifecycle import JarvisRuntime


EXIT_COMMANDS = {"exit", "quit", "q", "bye"}
TIMING_LAST_COMMANDS = {"timing last", "last timing", "show timing", "latency last"}


def main() -> None:
    runtime = JarvisRuntime()
    boot_result = runtime.boot()
    print(boot_result.message)
    print("Type 'exit' to stop Jarvis. Try: hello, status, list agents, screen check, timing last")

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


if __name__ == "__main__":
    main()
