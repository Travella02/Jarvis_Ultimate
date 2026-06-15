"""General conversation agent."""

from __future__ import annotations

from typing import Any

from jarvis.agents.conversation_agent.prompts import get_prompt_stats, get_system_prompt
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
            ability_registry = context.get("ability_registry")
            ability_count = ability_registry.count(enabled_only=True) if ability_registry is not None and hasattr(ability_registry, "count") else 0
            llm_provider = context.get("llm_provider")
            provider_name = getattr(llm_provider, "provider_name", "unknown") if llm_provider else "none"
            provider_model = getattr(llm_provider, "model", "unknown") if llm_provider else "none"
            streaming = getattr(llm_provider, "streaming_enabled", False) if llm_provider else False
            return JarvisResult.ok(
                f"Jarvis 3 core is online. Agent registry is active with {agent_count} enabled agents and {ability_count} registered abilities. LLM provider: {provider_name} ({provider_model}). Streaming: {'enabled' if streaming else 'disabled'}.",
                agent_name=self.name,
                action="status",
                data={"enabled_agent_count": agent_count, "enabled_ability_count": ability_count, "llm_provider": provider_name, "llm_model": provider_model, "llm_streaming": streaming},
            )

        if intent_name == "list_agents":
            if not registry:
                return JarvisResult.fail("The agent registry is not available.", agent_name=self.name, action="list_agents")
            agents = registry.enabled_records()
            lines = [f"{record.display_name} ({record.name})" for record in agents]
            ability_registry = context.get("ability_registry")
            ability_lines = []
            if ability_registry is not None and hasattr(ability_registry, "all"):
                ability_lines = [f"{ability.display_name} [{ability.agent_name}]" for ability in ability_registry.all(enabled_only=True)]
            message = "Available agents: " + "; ".join(lines)
            if ability_lines:
                message += ". Abilities: " + "; ".join(ability_lines)
            return JarvisResult.ok(
                message,
                agent_name=self.name,
                action="list_agents",
                data={"agents": [record.name for record in agents], "abilities": ability_lines},
            )

        return self._handle_general_chat(command, context=context)

    def _handle_general_chat(self, command: str, *, context: dict[str, Any]) -> JarvisResult:
        llm_provider = context.get("llm_provider")
        timing = context.get("timing")
        stream_callback = context.get("stream_callback")
        if llm_provider is None:
            return JarvisResult.ok(
                "I can route conversation now, but no LLM provider is attached yet.",
                agent_name=self.name,
                action="general_chat",
                data={"llm_enabled": False},
            )

        config = context.get("config")
        prompt_mode = getattr(config, "conversation_prompt_mode", "normal") if config else "normal"
        system_prompt = get_system_prompt(prompt_mode)
        prompt_stats = get_prompt_stats(prompt_mode)
        short_term_memory = context.get("short_term_memory")
        short_term_fact_memory = context.get("short_term_fact_memory")
        long_term_memory = context.get("long_term_memory")
        memory_messages = []
        if short_term_memory is not None and hasattr(short_term_memory, "to_llm_messages"):
            memory_messages = short_term_memory.to_llm_messages()
        memory_context_blocks: list[str] = []
        short_term_fact_context = ""
        if short_term_fact_memory is not None and hasattr(short_term_fact_memory, "relevant_context"):
            short_term_fact_context = short_term_fact_memory.relevant_context(command.strip())
            if short_term_fact_context:
                memory_context_blocks.append(short_term_fact_context)
        long_term_context = ""
        if long_term_memory is not None and hasattr(long_term_memory, "relevant_context"):
            long_term_context = long_term_memory.relevant_context(command.strip())
            if long_term_context:
                memory_context_blocks.append(long_term_context)
        if memory_context_blocks:
            system_prompt = (system_prompt or "").rstrip() + "\n\n" + "\n\n".join(memory_context_blocks) + "\nUse these memories only when they are relevant to the user's request."
        messages = [*memory_messages, {"role": "user", "content": command.strip()}]
        memory_turns = len(memory_messages) // 2
        short_term_facts_used = short_term_fact_context.count("\n-") if short_term_fact_context else 0
        long_term_memories_used = long_term_context.count("\n-") if long_term_context else 0
        self._mark(timing, "conversation.memory_context_selected", turns=memory_turns, messages=len(memory_messages), short_term_facts=short_term_facts_used, long_term_memories=long_term_memories_used)
        self._mark(timing, "conversation.prompt_selected", **prompt_stats)
        self._mark(timing, "conversation.llm_chat_start", stream_callback=stream_callback is not None, message_count=len(messages))
        response = llm_provider.chat(messages, system_prompt=system_prompt, timing=timing, stream_callback=stream_callback)
        did_stream = bool(response.raw.get("streamed")) if isinstance(response.raw, dict) else False
        self._mark(
            timing,
            "conversation.llm_chat_finished",
            success=response.success,
            provider=response.provider,
            model=response.model,
            streamed=did_stream,
        )

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
                    "streamed_output": did_stream,
                    "prompt_mode": prompt_stats["mode"],
                    "system_prompt_chars": prompt_stats["chars"],
                    "short_term_memory_turns_used": memory_turns,
                    "short_term_facts_used": short_term_facts_used,
                    "long_term_memories_used": long_term_memories_used,
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
                "streamed_output": did_stream,
                "prompt_mode": prompt_stats["mode"],
                "system_prompt_chars": prompt_stats["chars"],
                "short_term_memory_turns_used": memory_turns,
                "short_term_facts_used": short_term_facts_used,
                "long_term_memories_used": long_term_memories_used,
            },
        )

    def _mark(self, timing: Any | None, name: str, **data: Any) -> None:
        if timing is not None and hasattr(timing, "mark"):
            timing.mark(name, **data)
