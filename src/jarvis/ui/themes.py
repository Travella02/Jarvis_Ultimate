"""Theme tokens for Jarvis desktop clients.

The UI theme layer is intentionally framework-neutral: Tkinter, a future web
client, or a later game/3D avatar shell can all consume the same tokens.  The
first themes are dark/cyber variants designed to make Jarvis feel like a
futuristic control center while keeping the core runtime headless-capable.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Mapping

_REQUIRED_THEME_KEYS = {
    "name",
    "background",
    "surface",
    "surface_raised",
    "panel",
    "panel_alt",
    "panel_border",
    "panel_glow",
    "text",
    "text_soft",
    "muted",
    "accent",
    "accent_2",
    "accent_soft",
    "success",
    "warning",
    "error",
    "shadow",
    "font_family",
    "mono_font_family",
}

_THEME_BASE = {
    "name": "Jarvis Dark",
    "background": "#030712",
    "surface": "#050b18",
    "surface_raised": "#08111f",
    "panel": "#0b1220",
    "panel_alt": "#111827",
    "panel_border": "#164e63",
    "panel_glow": "#083344",
    "text": "#dbeafe",
    "text_soft": "#a5f3fc",
    "muted": "#7dd3fc",
    "accent": "#22d3ee",
    "accent_2": "#38bdf8",
    "accent_soft": "#0e7490",
    "success": "#34d399",
    "warning": "#fbbf24",
    "error": "#fb7185",
    "shadow": "#020617",
    "font_family": "Segoe UI",
    "mono_font_family": "Cascadia Mono",
}

_THEMES: dict[str, dict[str, str]] = {
    "jarvis_dark": dict(_THEME_BASE),
    "cyber_blue": {
        **_THEME_BASE,
        "name": "Cyber Blue",
        "background": "#020617",
        "surface": "#06101d",
        "surface_raised": "#0a1628",
        "panel": "#07111f",
        "panel_alt": "#0c1b2e",
        "panel_border": "#0ea5e9",
        "panel_glow": "#075985",
        "text": "#e0f2fe",
        "text_soft": "#bae6fd",
        "accent": "#38bdf8",
        "accent_2": "#22d3ee",
        "accent_soft": "#0284c7",
    },
    "stealth_black": {
        **_THEME_BASE,
        "name": "Stealth Black",
        "background": "#010409",
        "surface": "#050505",
        "surface_raised": "#0a0a0a",
        "panel": "#0b0f14",
        "panel_alt": "#111111",
        "panel_border": "#334155",
        "panel_glow": "#1e293b",
        "text": "#e5e7eb",
        "text_soft": "#cbd5e1",
        "muted": "#94a3b8",
        "accent": "#67e8f9",
        "accent_2": "#a78bfa",
        "accent_soft": "#475569",
    },
}

_STATE_COLORS = {
    "sleeping": "#155e75",
    "wake_listening": "#0891b2",
    "wake-listening": "#0891b2",
    "listening": "#22d3ee",
    "transcribing": "#60a5fa",
    "thinking": "#a78bfa",
    "speaking": "#34d399",
    "working": "#fbbf24",
    "error": "#fb7185",
    "idle": "#38bdf8",
}

_STATUS_COLORS = {
    "running": "success",
    "ready": "success",
    "enabled": "success",
    "sleeping": "accent_soft",
    "listening": "accent",
    "awake": "accent",
    "warming": "warning",
    "stopped": "muted",
    "disabled": "muted",
    "failed": "error",
    "error": "error",
}


def available_themes() -> list[str]:
    """Return available theme identifiers."""

    return sorted(_THEMES)


def validate_theme(theme: Mapping[str, str]) -> None:
    """Validate a theme mapping before a client consumes it."""

    missing = sorted(_REQUIRED_THEME_KEYS - set(theme))
    if missing:
        raise ValueError(f"Theme is missing required key(s): {', '.join(missing)}")


def get_theme(name: str = "jarvis_dark") -> dict[str, str]:
    """Return a copy of a registered theme.

    Unknown theme names intentionally fall back to jarvis_dark so desktop startup
    never fails because of a cosmetic setting.
    """

    key = str(name or "jarvis_dark").strip().lower().replace("-", "_")
    theme = deepcopy(_THEMES.get(key, _THEMES["jarvis_dark"]))
    validate_theme(theme)
    return theme


def state_color(state: str, theme: Mapping[str, str] | None = None) -> str:
    """Resolve an avatar/runtime state to a display color."""

    theme = theme or _THEMES["jarvis_dark"]
    return _STATE_COLORS.get(str(state).strip().lower(), theme["accent"])


def status_color(status: str, theme: Mapping[str, str] | None = None) -> str:
    """Resolve a status word to a theme color token value."""

    theme = theme or _THEMES["jarvis_dark"]
    lowered = str(status).strip().lower()
    for keyword, token in _STATUS_COLORS.items():
        if keyword in lowered:
            return theme.get(token, theme["accent"])
    return theme["muted"]


# Backwards-compatible name used by earlier patches/tests.
JARVIS_DARK_THEME = get_theme("jarvis_dark")
