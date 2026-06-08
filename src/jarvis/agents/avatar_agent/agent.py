"""Placeholder implementation for avatar_agent."""

from __future__ import annotations

from typing import Any

from jarvis.core.result import JarvisResult


class Agent:
    name = "avatar_agent"

    def __init__(self, *, manifest: dict[str, Any] | None = None, registry: Any | None = None) -> None:
        self.manifest = manifest or {}
        self.registry = registry

    def handle(self, command: str, context: dict[str, Any] | None = None) -> JarvisResult:
        return JarvisResult.ok(
            "Avatar Agent is registered and routed correctly, but its real tools are not implemented yet.",
            agent_name=self.name,
            action="placeholder_response",
            data={"command": command, "implemented": False, "next_step": "Implement this agent tools in a future milestone."},
        )
