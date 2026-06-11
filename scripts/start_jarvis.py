"""Start Jarvis Ultimate's full desktop body.

This launcher is the normal one-file entrypoint for daily use. It starts the
same Jarvis core runtime as the CLI, opens the desktop interface, warms voice
systems during boot when configured, and starts the background sleep/wake voice
runtime when desktop auto-start is enabled.
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.clients.desktop.app import main

if __name__ == "__main__":
    main()
