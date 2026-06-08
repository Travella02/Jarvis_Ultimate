"""Jarvis runtime boot/lifecycle helpers."""

from __future__ import annotations

from pathlib import Path

from jarvis.brain.router import JarvisRouter
from jarvis.core.config import JarvisConfig
from jarvis.core.events import EventBus
from jarvis.core.logging import JarvisLogger
from jarvis.core.registry import AgentRegistry
from jarvis.core.result import JarvisResult


class JarvisRuntime:
    """Boots the core Jarvis systems and handles user commands."""

    def __init__(self, *, project_root: str | Path | None = None) -> None:
        self.config = JarvisConfig.from_project_root(project_root)
        self.events = EventBus()
        self.logger = JarvisLogger(self.config.logs_dir)
        self.registry = AgentRegistry()
        self.router: JarvisRouter | None = None
        self.started = False

        self.events.subscribe("*", lambda event: self.logger.log_event(event.event_type, source=event.source, message=event.message, data=event.data))

    def boot(self) -> JarvisResult:
        self.events.emit("jarvis.boot_started", source="lifecycle", message="Jarvis boot started.")
        self.registry.load_builtin_agents()
        self.router = JarvisRouter(registry=self.registry, events=self.events)
        self.started = True
        agent_names = self.registry.names(enabled_only=True)
        result = JarvisResult.ok(
            f"Jarvis 3 is online. Registered {len(agent_names)} agents.",
            agent_name="lifecycle",
            action="boot",
            data={"agents": agent_names},
        )
        self.logger.log_result(result)
        self.events.emit("jarvis.boot_finished", source="lifecycle", message="Jarvis boot finished.", data=result.data)
        return result

    def handle_command(self, command: str) -> JarvisResult:
        if not self.started:
            self.boot()
        if self.router is None:
            return JarvisResult.fail("Jarvis router failed to initialize.", agent_name="lifecycle", action="handle_command")
        result = self.router.handle(command)
        self.logger.log_result(result)
        return result
