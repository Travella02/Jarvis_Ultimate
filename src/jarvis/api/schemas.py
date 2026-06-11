"""Small JSON schema helpers for Jarvis's local app-shell API."""

from __future__ import annotations

from typing import Any


def api_ok(data: dict[str, Any] | None = None, *, message: str = "ok") -> dict[str, Any]:
    return {"success": True, "message": message, "data": data or {}}


def api_error(message: str, *, status: int = 400, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"success": False, "message": message, "status": status, "data": data or {}}


def command_payload(command: str) -> dict[str, str]:
    return {"command": str(command or "").strip()}
