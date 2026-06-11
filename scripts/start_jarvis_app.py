"""Start Jarvis Ultimate's native app-shell interface.

This launcher starts the Python local API bridge, then opens the Electron
HTML/CSS/JS app shell when Electron is installed.  If Electron has not been
installed yet, it falls back to the existing Tkinter desktop body so Jarvis still
opens as a normal desktop app instead of a browser tab.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.api.local_server import make_local_api_server


def _npm_command() -> str | None:
    return shutil.which("npm.cmd") or shutil.which("npm")


def _electron_ready(shell_root: Path) -> bool:
    return (shell_root / "node_modules" / "electron").exists()


def _run_tkinter_fallback() -> None:
    print("Opening the existing Tkinter Jarvis desktop body as a fallback.")
    from jarvis.clients.desktop.app import main as desktop_main

    desktop_main()


def main() -> None:
    parser = argparse.ArgumentParser(description="Start the Jarvis native app shell.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-fallback", action="store_true", help="Exit instead of opening the Tkinter desktop fallback when Electron is unavailable.")
    args = parser.parse_args()

    shell_root = ROOT / "app_shell"
    npm = _npm_command()
    if not npm or not _electron_ready(shell_root):
        print("Electron app shell is present, but its Node dependencies are not installed yet.")
        print("To enable the HTML/CSS/JS native app shell, run:")
        print("  cd app_shell")
        print("  npm install")
        print("  cd ..")
        print("  python scripts\\start_jarvis_app.py")
        if args.no_fallback:
            raise SystemExit(1)
        _run_tkinter_fallback()
        return

    server, api = make_local_api_server(host=args.host, port=args.port, project_root=ROOT)
    api.boot()
    api_thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.25}, daemon=True)
    api_thread.start()

    env = os.environ.copy()
    env["JARVIS_API_URL"] = api.api_url
    env["JARVIS_PROJECT_ROOT"] = str(ROOT)
    print(f"Jarvis local API online at {api.api_url}")
    print("Opening Jarvis Ultimate native app shell...")
    try:
        subprocess.run([npm, "start"], cwd=shell_root, env=env, check=False)
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
