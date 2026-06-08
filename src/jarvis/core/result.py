"""Standard result and event models for Jarvis 3.

Every agent/tool should return a JarvisResult so the brain can handle success,
errors, confirmations, data, and UI/avatar events consistently.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    """Return an ISO timestamp in UTC."""
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class JarvisEvent:
    """A lightweight event emitted by Jarvis core, agents, tools, or UI."""

    event_type: str
    source: str = "system"
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class JarvisResult:
    """Standard response object returned by agents and tools."""

    success: bool
    message: str
    agent_name: str = "jarvis"
    action: str = "respond"
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    events: list[JarvisEvent] = field(default_factory=list)
    needs_confirmation: bool = False
    confirmation_prompt: str | None = None
    timestamp: str = field(default_factory=utc_now_iso)

    @classmethod
    def ok(
        cls,
        message: str,
        *,
        agent_name: str = "jarvis",
        action: str = "respond",
        data: dict[str, Any] | None = None,
        events: list[JarvisEvent] | None = None,
    ) -> "JarvisResult":
        return cls(
            success=True,
            message=message,
            agent_name=agent_name,
            action=action,
            data=data or {},
            events=events or [],
        )

    @classmethod
    def fail(
        cls,
        message: str,
        *,
        agent_name: str = "jarvis",
        action: str = "respond",
        errors: list[str] | None = None,
        data: dict[str, Any] | None = None,
    ) -> "JarvisResult":
        return cls(
            success=False,
            message=message,
            agent_name=agent_name,
            action=action,
            errors=errors or [message],
            data=data or {},
        )

    @classmethod
    def confirmation(
        cls,
        message: str,
        *,
        confirmation_prompt: str,
        agent_name: str = "jarvis",
        action: str = "confirm",
        data: dict[str, Any] | None = None,
    ) -> "JarvisResult":
        return cls(
            success=False,
            message=message,
            agent_name=agent_name,
            action=action,
            data=data or {},
            needs_confirmation=True,
            confirmation_prompt=confirmation_prompt,
        )

    def add_event(self, event_type: str, *, source: str | None = None, message: str = "", data: dict[str, Any] | None = None) -> None:
        self.events.append(
            JarvisEvent(
                event_type=event_type,
                source=source or self.agent_name,
                message=message,
                data=data or {},
            )
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["events"] = [event.to_dict() for event in self.events]
        return result
