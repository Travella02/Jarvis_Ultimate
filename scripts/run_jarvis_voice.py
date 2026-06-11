from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.clients.cli.cli_client import main

if __name__ == "__main__":
    # This script uses the same CLI entrypoint, but the 0.1.5 installer enables
    # startup sleep/wake mode in .env so Jarvis immediately enters always-listening
    # sleep mode after boot/warmup.
    main()
