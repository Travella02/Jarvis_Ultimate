"""Jarvis runtime boot/lifecycle helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.brain.router import JarvisRouter
from jarvis.core.config import JarvisConfig
from jarvis.core.events import EventBus
from jarvis.core.logging import JarvisLogger
from jarvis.core.registry import AgentRegistry
from jarvis.core.result import JarvisResult
from jarvis.core.timing import TurnTimer, format_timing_summary
from jarvis.providers.llm.base import LLMStreamCallback
from jarvis.providers.llm.factory import create_llm_provider


class JarvisRuntime:
    """Boots the core Jarvis systems and handles user commands."""

    def __init__(self, *, project_root: str | Path | None = None, llm_provider: Any | None = None) -> None:
        self.config = JarvisConfig.from_project_root(project_root)
        self.events = EventBus()
        self.logger = JarvisLogger(self.config.logs_dir)
        self.registry = AgentRegistry()
        self.llm_provider = llm_provider or create_llm_provider(self.config)
        self.router: JarvisRouter | None = None
        self.started = False
        self.last_timing: TurnTimer | None = None

        self.events.subscribe("*", lambda event: self.logger.log_event(event.event_type, source=event.source, message=event.message, data=event.data))

    def boot(self) -> JarvisResult:
        self.events.emit("jarvis.boot_started", source="lifecycle", message="Jarvis boot started.")
        self.registry.load_builtin_agents()
        self.router = JarvisRouter(registry=self.registry, events=self.events, llm_provider=self.llm_provider)
        self.started = True
        agent_names = self.registry.names(enabled_only=True)
        result = JarvisResult.ok(
            f"Jarvis 3 is online. Registered {len(agent_names)} agents.",
            agent_name="lifecycle",
            action="boot",
            data={
                "agents": agent_names,
                "llm_provider": getattr(self.llm_provider, "provider_name", "unknown"),
                "llm_model": getattr(self.llm_provider, "model", "unknown"),
                "llm_streaming": getattr(self.llm_provider, "streaming_enabled", False),
            },
        )
        self.logger.log_result(result)
        self.events.emit("jarvis.boot_finished", source="lifecycle", message="Jarvis boot finished.", data=result.data)
        return result

    def handle_command(self, command: str, *, stream_callback: LLMStreamCallback | None = None) -> JarvisResult:
        if not self.started:
            self.boot()
        if self.router is None:
            return JarvisResult.fail("Jarvis router failed to initialize.", agent_name="lifecycle", action="handle_command")

        timing = TurnTimer(command=command)
        timing.mark("runtime.handle_command_start", stream_callback=stream_callback is not None)
        result = self.router.handle(command, timing=timing, stream_callback=stream_callback)
        timing.mark("runtime.handle_command_finished", success=result.success, action=result.action, streamed=result.data.get("streamed_output"))
        result.data["timing"] = timing.to_dict()
        self.last_timing = timing
        self.logger.log_result(result)
        return result

    def timing_last(self) -> str:
        """Return a readable summary for the most recent command turn."""
        return format_timing_summary(self.last_timing)
