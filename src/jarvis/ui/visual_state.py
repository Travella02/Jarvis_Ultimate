"""UI visual state engine for Jarvis's desktop body.

The visual state engine is intentionally framework-neutral.  Tkinter, a future
web UI, or a future WebGL/3D avatar renderer can all consume the same state
profile without needing to know about voice-loop implementation details.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class OrbVisualProfile:
    """Animation/style hints for a Jarvis orb state."""

    state: str
    label: str
    color_role: str
    pulse_speed: float
    ring_speed: float
    core_scale: float
    glow_strength: float
    particle_count: int
    breathing: bool = False


_STATE_ALIASES: dict[str, str] = {
    "sleep": "sleeping",
    "sleeping": "sleeping",
    "wake_listening": "wake_listening",
    "wake-listening": "wake_listening",
    "listening for wake word": "wake_listening",
    "listening": "listening",
    "awake": "listening",
    "transcribing": "transcribing",
    "thinking": "thinking",
    "speaking": "speaking",
    "working": "working",
    "tool_active": "working",
    "idle": "idle",
    "ready": "idle",
    "error": "error",
}

_ORB_PROFILES: dict[str, OrbVisualProfile] = {
    "sleeping": OrbVisualProfile("sleeping", "Sleep Mode", "sleeping", 0.25, 0.18, 0.85, 0.55, 8, True),
    "wake_listening": OrbVisualProfile("wake_listening", "Listening for Wake Word", "wake_listening", 0.45, 0.32, 0.92, 0.75, 12, True),
    "listening": OrbVisualProfile("listening", "Listening", "listening", 0.75, 0.45, 1.0, 0.9, 16, True),
    "transcribing": OrbVisualProfile("transcribing", "Transcribing", "transcribing", 1.0, 0.85, 1.02, 0.95, 18, False),
    "thinking": OrbVisualProfile("thinking", "Thinking", "thinking", 1.3, 1.6, 1.06, 1.0, 24, False),
    "speaking": OrbVisualProfile("speaking", "Speaking", "speaking", 1.55, 1.15, 1.08, 1.0, 22, False),
    "working": OrbVisualProfile("working", "Working", "working", 1.05, 1.25, 1.05, 0.95, 20, False),
    "idle": OrbVisualProfile("idle", "Ready", "idle", 0.35, 0.25, 0.9, 0.65, 10, True),
    "error": OrbVisualProfile("error", "Attention Required", "error", 0.9, 0.2, 0.95, 1.0, 6, False),
}


def normalize_visual_state(state: str | None) -> str:
    """Normalize a raw avatar/runtime state into a known visual state."""

    key = str(state or "idle").strip().lower().replace(" ", "_")
    return _STATE_ALIASES.get(key, key if key in _ORB_PROFILES else "idle")


def orb_profile_for_state(state: str | None) -> OrbVisualProfile:
    """Return the animation profile for a state, falling back safely."""

    return _ORB_PROFILES[normalize_visual_state(state)]


def classify_voice_status(message: str) -> str:
    """Classify a voice-loop status line into a visual state.

    This keeps desktop status callbacks from duplicating string matching logic
    and gives future UI clients a shared state model.
    """

    text = str(message or "").lower()
    if "error" in text or "failed" in text:
        return "error"
    if "returning to sleep" in text or "sleep mode" in text or "staying asleep" in text:
        return "sleeping"
    if "wake phrase" in text or "sleeping" in text:
        return "wake_listening"
    if "wake detected" in text or "jarvis is awake" in text or "awake" in text:
        return "listening"
    if "transcrib" in text or "heard" in text:
        return "transcribing"
    if "thinking" in text or "routing" in text:
        return "thinking"
    if "speaking" in text or "generated speech" in text:
        return "speaking"
    if "warming" in text or "working" in text:
        return "working"
    return "listening"


def state_label(state: str | None) -> str:
    """Human-readable state label for compact status displays."""

    return orb_profile_for_state(state).label


def available_visual_states() -> tuple[str, ...]:
    """Return known visual states in display order."""

    return tuple(_ORB_PROFILES.keys())


def profile_summary(profile: OrbVisualProfile | Mapping[str, object]) -> dict[str, object]:
    """Return a serializable summary of an orb profile for tests/debug panels."""

    if isinstance(profile, OrbVisualProfile):
        return {
            "state": profile.state,
            "label": profile.label,
            "color_role": profile.color_role,
            "pulse_speed": profile.pulse_speed,
            "ring_speed": profile.ring_speed,
            "core_scale": profile.core_scale,
            "glow_strength": profile.glow_strength,
            "particle_count": profile.particle_count,
            "breathing": profile.breathing,
        }
    return dict(profile)
