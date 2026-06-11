"""Dependency-free local HTTP API for Jarvis's native app shell.

This is intentionally a small standard-library server.  It gives the Electron
HTML/CSS/JS interface a stable bridge to the existing Python runtime without
forcing FastAPI, Flask, websockets, or any other dependency into the project yet.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
from typing import Any
from urllib.parse import urlparse

from jarvis.api.schemas import api_error, api_ok
from jarvis.clients.app_shell.bridge import DEFAULT_API_URL, build_app_shell_snapshot
from jarvis.core.lifecycle import JarvisRuntime
from jarvis.ui.workspace import UIWorkspaceState


class LocalJarvisAPI:
    """Stateful local bridge between the app shell and JarvisRuntime."""

    def __init__(self, *, runtime: JarvisRuntime | None = None, project_root: str | Path | None = None, api_url: str = DEFAULT_API_URL) -> None:
        self.runtime = runtime or JarvisRuntime(project_root=project_root)
        self.workspace = UIWorkspaceState()
        self.api_url = api_url
        self._lock = threading.RLock()
        self._booted = bool(getattr(self.runtime, "started", False))
        self.runtime.events.subscribe("*", self._on_runtime_event)

    @property
    def booted(self) -> bool:
        return self._booted

    def boot(self) -> None:
        with self._lock:
            if self._booted:
                return
            result = self.runtime.boot()
            self.workspace.add_chat_message("jarvis", result.message)
            for record in self.runtime.registry.enabled_records():
                self.workspace.set_agent_status(record.name, "registered")
            self.workspace.add_notice("Local app-shell API bridge initialized.")
            self._booted = True

    def health(self) -> dict[str, Any]:
        return {
            "name": "Jarvis Ultimate Local API",
            "booted": self._booted,
            "api_url": self.api_url,
            "runtime_started": bool(getattr(self.runtime, "started", False)),
        }

    def snapshot(self) -> dict[str, Any]:
        self.boot()
        with self._lock:
            return build_app_shell_snapshot(self.workspace, self.runtime, api_url=self.api_url, bridge_status="online")

    def events(self) -> list[dict[str, Any]]:
        self.boot()
        with self._lock:
            return [event.to_dict() for event in list(self.workspace.events)]

    def handle_command(self, command: str) -> dict[str, Any]:
        command = str(command or "").strip()
        if not command:
            return api_error("Command cannot be empty.", status=400)

        self.boot()
        with self._lock:
            self.workspace.add_chat_message("user", command)
            self.workspace.avatar.set_state("thinking", expression="focused", message="Routing command from app shell...")

        chunks: list[str] = []

        def on_chunk(chunk: str) -> None:
            chunks.append(chunk)
            with self._lock:
                self.workspace.avatar.set_state("speaking", expression="active", message="Streaming response to app shell...")

        try:
            result = self.runtime.handle_command(command, stream_callback=on_chunk)
            response_text = "".join(chunks).strip() or result.message
            with self._lock:
                self.workspace.add_chat_message("jarvis", response_text)
                next_state = "idle" if result.success else "error"
                expression = "neutral" if result.success else "alert"
                message = "Ready, sir." if result.success else result.message
                self.workspace.avatar.set_state(next_state, expression=expression, message=message)
            return api_ok({"result": result.to_dict(), "response_text": response_text, "state": self.snapshot()}, message=result.message)
        except Exception as exc:  # pragma: no cover - defensive API boundary
            with self._lock:
                self.workspace.avatar.set_state("error", expression="alert", message=str(exc))
                self.workspace.add_chat_message("jarvis", f"App-shell API error, sir: {exc}")
            return api_error(f"Jarvis API command failed: {exc}", status=500, data={"state": self.snapshot()})

    def _on_runtime_event(self, event: Any) -> None:
        with self._lock:
            self.workspace.apply_event(event)


def _json_bytes(payload: dict[str, Any] | list[Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")


def make_handler(api: LocalJarvisAPI) -> type[BaseHTTPRequestHandler]:
    class JarvisLocalAPIHandler(BaseHTTPRequestHandler):
        server_version = "JarvisLocalAPI/0.1.7"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - stdlib signature
            return

        def _send(self, payload: dict[str, Any] | list[Any], *, status: int = 200) -> None:
            body = _json_bytes(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:  # noqa: N802 - stdlib hook
            self._send(api_ok(message="ok"))

        def do_GET(self) -> None:  # noqa: N802 - stdlib hook
            path = urlparse(self.path).path.rstrip("/") or "/"
            if path == "/api/health":
                self._send(api_ok(api.health(), message="online"))
                return
            if path == "/api/state":
                self._send(api_ok(api.snapshot(), message="state"))
                return
            if path == "/api/events":
                self._send(api_ok({"events": api.events()}, message="events"))
                return
            self._send(api_error("Unknown API route.", status=404), status=404)

        def do_POST(self) -> None:  # noqa: N802 - stdlib hook
            path = urlparse(self.path).path.rstrip("/") or "/"
            if path != "/api/command":
                self._send(api_error("Unknown API route.", status=404), status=404)
                return

            length = int(self.headers.get("Content-Length", "0") or 0)
            raw_body = self.rfile.read(length) if length > 0 else b"{}"
            try:
                payload = json.loads(raw_body.decode("utf-8"))
            except json.JSONDecodeError:
                self._send(api_error("Request body must be valid JSON.", status=400), status=400)
                return
            command = str(payload.get("command", "")).strip() if isinstance(payload, dict) else ""
            response = api.handle_command(command)
            self._send(response, status=int(response.get("status", 200) if not response.get("success", True) else 200))

    return JarvisLocalAPIHandler


def make_local_api_server(
    *,
    host: str = "127.0.0.1",
    port: int = 8765,
    project_root: str | Path | None = None,
    runtime: JarvisRuntime | None = None,
) -> tuple[ThreadingHTTPServer, LocalJarvisAPI]:
    api_url = f"http://{host}:{port}"
    api = LocalJarvisAPI(runtime=runtime, project_root=project_root, api_url=api_url)
    server = ThreadingHTTPServer((host, port), make_handler(api))
    actual_host, actual_port = server.server_address[:2]
    api.api_url = f"http://{actual_host}:{actual_port}"
    return server, api


def run_local_api_server(*, host: str = "127.0.0.1", port: int = 8765, project_root: str | Path | None = None) -> None:
    server, api = make_local_api_server(host=host, port=port, project_root=project_root)
    api.boot()
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        server.server_close()
