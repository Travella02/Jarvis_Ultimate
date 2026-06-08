"""General conversation agent."""

from __future__ import annotations

from typing import Any

from jarvis.agents.conversation_agent.prompts import SYSTEM_PROMPT
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
                "I did not catch a command. Type something like 'status', 'list agents', or just talk to me normally.",
                agent_name=self.name,
                action="empty_input",
            )

        if intent_name == "status":
            agent_count = len(registry.enabled_records()) if registry else 0
            llm_provider = context.get("llm_provider")
            provider_name = getattr(llm_provider, "provider_name", "unknown") if llm_provider else "none"
            provider_model = getattr(llm_provider, "model", "unknown") if llm_provider else "none"
            return JarvisResult.ok(
                f"Jarvis 3 core is online. Agent registry is active with {agent_count} enabled agents. LLM provider: {provider_name} ({provider_model}).",
                agent_name=self.name,
                action="status",
                data={"enabled_agent_count": agent_count, "llm_provider": provider_name, "llm_model": provider_model},
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

        return self._handle_general_chat(command, context=context)

    def _handle_general_chat(self, command: str, *, context: dict[str, Any]) -> JarvisResult:
        llm_provider = context.get("llm_provider")
        timing = context.get("timing")
        if llm_provider is None:
            return JarvisResult.ok(
                "I can route conversation now, but no LLM provider is attached yet.",
                agent_name=self.name,
                action="general_chat",
                data={"llm_enabled": False},
            )

        messages = [{"role": "user", "content": command.strip()}]
        self._mark(timing, "conversation.llm_chat_start")
        response = llm_provider.chat(messages, system_prompt=SYSTEM_PROMPT, timing=timing)
        self._mark(timing, "conversation.llm_chat_finished", success=response.success, provider=response.provider, model=response.model)

        provider_name = getattr(llm_provider, "provider_name", response.provider)
        if response.success:
            return JarvisResult.ok(
                response.content,
                agent_name=self.name,
                action="llm_chat",
                data={
                    "llm_enabled": True,
                    "llm_provider": provider_name,
                    "llm_model": response.model,
                },
            )

        return JarvisResult.fail(
            "I tried to talk through LM Studio, but the local model provider is not responding yet. "
            "Open LM Studio, load your model, start the Local Server, then try again. "
            f"Details: {response.error}",
            agent_name=self.name,
            action="llm_chat",
            errors=[response.error or "Unknown LLM provider error."],
            data={
                "llm_enabled": False,
                "llm_provider": provider_name,
                "llm_model": response.model,
            },
        )

    def _mark(self, timing: Any | None, name: str, **data: Any) -> None:
        if timing is not None and hasattr(timing, "mark"):
            timing.mark(name, **data)
