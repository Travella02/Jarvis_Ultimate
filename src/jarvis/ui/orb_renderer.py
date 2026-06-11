"""Framework-neutral helpers for Jarvis's advanced orb renderer.

The desktop currently renders the orb with Tkinter canvas primitives, but the
math/color helpers in this module are deliberately UI-framework neutral so a
future WebGL/Qt/VRM renderer can reuse the same state-driven design language.
"""

from __future__ import annotations

import math
from typing import Mapping


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    text = str(value or "#000000").strip()
    if text.startswith("#"):
        text = text[1:]
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) != 6:
        return (0, 0, 0)
    try:
        return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))
    except ValueError:
        return (0, 0, 0)


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = (max(0, min(255, int(part))) for part in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


def blend_hex(a: str, b: str, amount: float) -> str:
    """Blend two hex colors.

    amount=0 returns a, amount=1 returns b.
    """

    amount = clamp(amount)
    ar, ag, ab = hex_to_rgb(a)
    br, bg, bb = hex_to_rgb(b)
    return rgb_to_hex((ar + (br - ar) * amount, ag + (bg - ag) * amount, ab + (bb - ab) * amount))


def state_orb_palette(state: str, theme: Mapping[str, str]) -> dict[str, str]:
    """Return a solid-orb palette for a visual state."""

    accent = str(theme.get("accent", "#00E5FF"))
    sleeping = str(theme.get("sleeping", theme.get("accent_soft", "#315A75")))
    wake = str(theme.get("wake_listening", accent))
    listening = str(theme.get("listening", accent))
    transcribing = str(theme.get("transcribing", "#38BDF8"))
    thinking = str(theme.get("thinking", "#E0F7FF"))
    speaking = str(theme.get("speaking", "#8B5CF6"))
    working = str(theme.get("working", "#35FFB6"))
    error = str(theme.get("error", "#FF4D6D"))

    base_by_state = {
        "sleeping": sleeping,
        "wake_listening": wake,
        "listening": listening,
        "transcribing": transcribing,
        "thinking": thinking,
        "speaking": speaking,
        "working": working,
        "idle": accent,
        "error": error,
    }
    base = base_by_state.get(state, accent)
    panel = str(theme.get("panel", "#08111F"))
    background = str(theme.get("background", "#020711"))
    white = "#F2FDFF"
    return {
        "base": base,
        "outer": blend_hex(background, base, 0.18),
        "shadow": blend_hex(background, base, 0.06),
        "mid": blend_hex(panel, base, 0.55),
        "core": blend_hex(base, white, 0.28),
        "highlight": blend_hex(base, white, 0.74),
        "ring": blend_hex(base, white, 0.42),
        "particle": blend_hex(base, white, 0.60),
        "dark_glass": blend_hex(background, base, 0.11),
    }


def solid_orb_layers(radius: int, state: str, theme: Mapping[str, str], *, layer_count: int = 34) -> list[dict[str, object]]:
    """Return outer-to-inner layers for a pseudo-3D solid orb.

    Each layer is a circle radius plus a color.  Rendering many translucent-looking
    solid layers creates a more dimensional orb in Tkinter without requiring a 3D
    engine yet.
    """

    palette = state_orb_palette(state, theme)
    layers: list[dict[str, object]] = []
    count = max(8, layer_count)
    for index in range(count):
        t = index / (count - 1)
        # Bias the center brighter so it feels like a lit, solid sphere.
        bright = t ** 1.55
        color = blend_hex(palette["outer"], palette["core"], bright)
        if index > count * 0.68:
            color = blend_hex(color, palette["highlight"], (t - 0.68) / 0.32 * 0.35)
        layer_radius = max(2, int(radius * (1.0 - 0.82 * t)))
        offset_x = int(-radius * 0.13 * t)
        offset_y = int(-radius * 0.16 * t)
        layers.append({"radius": layer_radius, "fill": color, "offset_x": offset_x, "offset_y": offset_y})
    return layers


def orb_highlights(radius: int, state: str, theme: Mapping[str, str]) -> list[dict[str, object]]:
    """Return highlight/glass marks for the solid orb."""

    palette = state_orb_palette(state, theme)
    return [
        {"kind": "oval", "dx": -0.36, "dy": -0.38, "rx": 0.23, "ry": 0.12, "fill": blend_hex(palette["highlight"], "#FFFFFF", 0.25)},
        {"kind": "arc", "dx": -0.04, "dy": -0.10, "rx": 0.74, "ry": 0.56, "outline": blend_hex(palette["ring"], "#FFFFFF", 0.18)},
        {"kind": "arc", "dx": 0.10, "dy": 0.14, "rx": 0.58, "ry": 0.42, "outline": blend_hex(palette["base"], "#FFFFFF", 0.08)},
    ]


def orbital_ring_plan(radius: int, tick: int, ring_speed: float) -> list[dict[str, object]]:
    """Return ring plan values for rotating pseudo-3D orbitals."""

    speed = max(0.05, float(ring_speed or 0.1))
    return [
        {"rx": radius + 42, "ry": int((radius + 42) * 0.34), "start": (tick * speed * 1.7 + 20) % 360, "extent": 245, "width": 3},
        {"rx": radius + 34, "ry": int((radius + 34) * 0.64), "start": (tick * speed * -1.25 + 250) % 360, "extent": 168, "width": 2},
        {"rx": radius + 10, "ry": int((radius + 10) * 0.88), "start": (tick * speed * 2.15 + 120) % 360, "extent": 118, "width": 2},
        {"rx": radius - 12, "ry": int((radius - 12) * 0.48), "start": (tick * speed * -2.6 + 310) % 360, "extent": 92, "width": 1},
    ]


def particle_positions(count: int, tick: int, ring_speed: float, radius: int) -> list[dict[str, float]]:
    """Return particle positions around an isometric orbit."""

    items: list[dict[str, float]] = []
    count = max(0, min(int(count), 36))
    phase = (tick / 360.0) * math.tau * max(float(ring_speed or 0.1), 0.05)
    for index in range(count):
        angle = phase + math.tau * index / max(count, 1)
        orbit = radius + 34 + (index % 5) * 7
        items.append({
            "x": math.cos(angle) * orbit,
            "y": math.sin(angle) * orbit * 0.50,
            "size": 1.2 + (index % 4) * 0.65,
        })
    return items


def renderer_capabilities() -> tuple[str, ...]:
    """Describe the current renderer for docs/tests/status panels."""

    return (
        "solid_layered_orb",
        "pseudo_3d_highlights",
        "rotating_orbital_rings",
        "state_reactive_motion",
        "particle_orbitals",
        "future_3d_renderer_ready",
    )
