"""Small JSON response helpers for Jarvis's local app-shell API."""

from __future__ import annotations

from typing import Any


def api_ok(data: dict[str, Any] | None = None, *, message: str = "ok", status: int = 200) -> dict[str, Any]:
    body = dict(data or {})
    payload: dict[str, Any] = {
        "success": True,
        "status": status,
        "message": message,
        "data": body,
    }
    payload.update(body)
    return payload


def api_error(message: str, *, status: int = 400, data: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "success": False,
        "status": status,
        "message": message,
        "errors": [message],
    }
    if data:
        payload.update(data)
    return payload
