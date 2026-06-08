"""General conversation agent."""

from __future__ import annotations

from typing import Any

from jarvis.core.registry import AgentRegistry
from jarvis.core.result import JarvisResult


class Agent:
    name = "conversation_agent"

    def __init__(self, *, manifest: dict[str, Any] | None = None, registry: AgentRegistry | None = None) -> None:
        self.manifest = manifest or {}
        self.registry = registry

    def handle(self, command: str, context: dict[str, Any] | None = None) -> JarvisResult:
        context = context or {}
        intent = context.get("intent")
        intent_name = getattr(intent, "intent", "general_chat")
        registry = context.get("registry") or self.registry

        if intent_name == "empty":
            return JarvisResult.ok(
                "I did not catch a command. Type something like 'status' or 'list agents'.",
                agent_name=self.name,
                action="empty_input",
            )

        if intent_name == "status":
            agent_count = len(registry.enabled_records()) if registry else 0
            return JarvisResult.ok(
                f"Jarvis 3 core is online. Agent registry is active with {agent_count} enabled agents.",
                agent_name=self.name,
                action="status",
                data={"enabled_agent_count": agent_count},
            )

        if intent_name == "list_agents":
            if not registry:
                return JarvisResult.fail("The agent registry is not available.", agent_name=self.name, action="list_agents")
            agents = registry.enabled_records()
            lines = [f"{record.display_name} ({record.name})" for record in agents]
            return JarvisResult.ok(
                "Available agents: " + "; ".join(lines),
                agent_name=self.name,
                action="list_agents",
                data={"agents": [record.name for record in agents]},
            )

        text = command.strip()
        if text.lower() in {"hello", "hi", "hey", "hey jarvis", "hello jarvis"}:
            message = "Hey Tanner. Jarvis 3 is online. The new core, registry, and routing foundation are active."
        else:
            message = "I can respond through the new Jarvis 3 routing system now. The real local LLM provider comes next."

        return JarvisResult.ok(
            message,
            agent_name=self.name,
            action="general_chat",
            data={"llm_enabled": False, "note": "Mock/general conversation only in 0.0.2."},
        )
