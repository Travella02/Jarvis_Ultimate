"""Avatar state model for the future desktop UI/body."""

from __future__ import annotations

from dataclasses import dataclass


VALID_AVATAR_STATES = {"idle", "listening", "thinking", "speaking", "error"}


@dataclass(slots=True)
class AvatarState:
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
