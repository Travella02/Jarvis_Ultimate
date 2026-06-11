"""Start Jarvis's local app-shell API server."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.api.local_server import run_local_api_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the Jarvis local API bridge for the native app shell.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print(f"Jarvis local app-shell API starting at http://{args.host}:{args.port}")
    run_local_api_server(host=args.host, port=args.port, project_root=ROOT)


if __name__ == "__main__":
    main()
