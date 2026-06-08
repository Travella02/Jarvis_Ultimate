"""CLI client for Jarvis 3."""

from __future__ import annotations

from jarvis.core.lifecycle import JarvisRuntime


EXIT_COMMANDS = {"exit", "quit", "q", "bye"}


def main() -> None:
    runtime = JarvisRuntime()
    boot_result = runtime.boot()
    print(boot_result.message)
    print("Type 'exit' to stop Jarvis. Try: hello, status, list agents, screen check")

    while True:
        try:
            command = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nJarvis: Shutting down.")
            break

        if command.lower() in EXIT_COMMANDS:
            print("Jarvis: Shutting down.")
            break

        result = runtime.handle_command(command)
        print(f"Jarvis: {result.message}")


if __name__ == "__main__":
    main()
