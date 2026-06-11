"""Small formatting helpers for Jarvis UI components.

These helpers keep panel/card formatting reusable and easy to test.  The Tkinter
client uses them today; future web/desktop clients can use the same model-level
formatters or replace only the rendering layer.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


def status_badge(label: str, value: str) -> str:
    """Format a compact status badge for text-based UI panels."""

    return f"[{label}: {value}]"


def panel_header(title: str, icon: str = "") -> str:
    """Return a consistent panel header string."""

    icon = f"{icon} " if icon else ""
    return f"{icon}{title}".strip().upper()


def format_key_value_rows(rows: Mapping[str, Any] | Iterable[tuple[str, Any]]) -> list[str]:
    """Format key/value data for workspace and debug panels."""

    items = rows.items() if isinstance(rows, Mapping) else rows
    return [f"{key}: {value}" for key, value in items]


def summarize_payload(payload: Mapping[str, Any], *, max_items: int = 6) -> list[str]:
    """Create a short human-readable preview for a dynamic panel payload."""

    if not payload:
        return ["No panel payload yet."]
    lines: list[str] = []
    for index, (key, value) in enumerate(payload.items()):
        if index >= max_items:
            lines.append(f"… {len(payload) - max_items} more field(s)")
            break
        rendered = value
        if isinstance(value, (list, tuple)):
            rendered = f"{len(value)} item(s)"
        elif isinstance(value, dict):
            rendered = f"{len(value)} field(s)"
        lines.append(f"{key}: {rendered}")
    return lines


def format_workspace_card(card: Mapping[str, Any]) -> str:
    """Format a workspace card summary."""

    return f"• {card.get('title', 'Untitled')} [{card.get('type', 'card')}]"
