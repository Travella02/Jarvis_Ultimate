"""Jarvis 3 main entrypoint."""

from __future__ import annotations

from jarvis.core.lifecycle import JarvisRuntime


def main() -> None:
    runtime = JarvisRuntime()
    result = runtime.boot()
    print(result.message)


if __name__ == "__main__":
    main()
