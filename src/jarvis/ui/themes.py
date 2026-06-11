"""Theme tokens for Jarvis desktop clients."""

from __future__ import annotations

JARVIS_DARK_THEME = {
    "background": "#05070d",
    "panel": "#0c1220",
    "panel_alt": "#111827",
    "text": "#dbeafe",
    "muted": "#7dd3fc",
    "accent": "#22d3ee",
    "accent_soft": "#0e7490",
    "success": "#34d399",
    "warning": "#fbbf24",
    "error": "#fb7185",
}


def get_theme(name: str = "jarvis_dark") -> dict[str, str]:
    return dict(JARVIS_DARK_THEME)
