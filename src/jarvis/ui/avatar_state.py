"""Avatar state model for Jarvis's desktop body/interface."""

from __future__ import annotations

from dataclasses import dataclass


VALID_AVATAR_STATES = {
    "idle",
    "sleeping",
    "wake_listening",
    "listening",
    "transcribing",
    "thinking",
    "speaking",
    "working",
    "error",
}

STATE_LABELS = {
    "idle": "Idle",
    "sleeping": "Sleeping",
    "wake_listening": "Listening for wake word",
    "listening": "Listening",
    "transcribing": "Transcribing",
    "thinking": "Thinking",
    "speaking": "Speaking",
    "working": "Working",
    "error": "Error",
}


@dataclass(slots=True)
class AvatarState:
    """Small serializable state object for any future avatar/body renderer.

    This intentionally stays UI-framework neutral so the same state can drive a
    Tkinter orb now, then a Live2D/VRM/web UI later.
    """

    state: str = "idle"
    expression: str = "neutral"
    message: str = ""

    def set_state(self, state: str, *, expression: str | None = None, message: str = "") -> None:
        if state not in VALID_AVATAR_STATES:
            raise ValueError(f"Invalid avatar state: {state}")
        self.state = state
        if expression is not None:
            self.expression = expression
        self.message = message

    @property
    def label(self) -> str:
        return STATE_LABELS.get(self.state, self.state.replace("_", " ").title())

    def to_dict(self) -> dict[str, str]:
        return {"state": self.state, "label": self.label, "expression": self.expression, "message": self.message}
