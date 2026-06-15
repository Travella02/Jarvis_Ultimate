"""Jarvis brain router."""

from __future__ import annotations

from typing import Any

from jarvis.brain.intent_classifier import IntentClassifier
from jarvis.core.events import EventBus
from jarvis.core.registry import AgentRegistry
from jarvis.core.result import JarvisResult
from jarvis.providers.llm.base import LLMStreamCallback


INTENT_AGENT_MAP = {
    "general_chat": "conversation_agent",
    "status": "conversation_agent",
    "list_agents": "conversation_agent",
    "empty": "conversation_agent",
    "screen_question": "screen_agent",
    "app_control": "app_agent",
    "voice_control": "voice_agent",
    "avatar_control": "avatar_agent",
    "memory_write": "memory_agent",
    "memory_search": "memory_agent",
    "file_task": "file_agent",
    "recording_task": "recorder_agent",
    "weather_lookup": "weather_agent",
}


class JarvisRouter:
    """Routes user commands to normal conversation or a specialized agent."""

    def __init__(
        self,
        *,
        registry: AgentRegistry,
        events: EventBus | None = None,
        classifier: IntentClassifier | None = None,
        llm_provider: Any | None = None,
        config: Any | None = None,
        short_term_memory: Any | None = None,
        long_term_memory: Any | None = None,
        ability_registry: Any | None = None,
    ) -> None:
        self.registry = registry
        self.events = events or EventBus()
        self.classifier = classifier or IntentClassifier()
        self.llm_provider = llm_provider
        self.config = config
        self.short_term_memory = short_term_memory
        self.long_term_memory = long_term_memory
        self.ability_registry = ability_registry

    def handle(self, command: str, *, timing: Any | None = None, stream_callback: LLMStreamCallback | None = None) -> JarvisResult:
        self._mark(timing, "brain.router_received")
        self.events.emit("user.command.received", source="brain.router", message=command)
        self.events.emit("brain.routing_started", source="brain.router")

        self._mark(timing, "brain.classify_start")
        intent = self.classifier.classify(command)
        agent_name = INTENT_AGENT_MAP.get(intent.intent, "conversation_agent")
        ability_selection = None
        if self.ability_registry is not None and hasattr(self.ability_registry, "select_for_command"):
            ability_selection = self.ability_registry.select_for_command(command, intent=intent.intent)
            if getattr(ability_selection, "ability", None) is None and intent.intent == "general_chat":
                fallback_selection = self.ability_registry.select_for_command(command, intent=None)
                fallback_ability = getattr(fallback_selection, "ability", None)
                if fallback_ability is not None and fallback_selection.confidence >= 0.72 and fallback_ability.agent_name != "conversation_agent":
                    ability_selection = fallback_selection
                    agent_name = fallback_ability.agent_name
        self._mark(timing, "brain.classify_finished", intent=intent.intent, agent_name=agent_name)
        self.events.emit(
            "brain.intent_classified",
            source="brain.router",
            data={"intent": intent.intent, "confidence": intent.confidence, "reason": intent.reason, "agent_name": agent_name, "ability_selection": ability_selection.to_dict() if ability_selection else None},
        )

        self._mark(timing, "brain.agent_lookup_start", agent_name=agent_name)
        agent = self.registry.get_agent(agent_name)
        self._mark(timing, "brain.agent_lookup_finished", found=agent is not None, agent_name=agent_name)
        if agent is None:
            result = JarvisResult.fail(
                f"I understood the intent as '{intent.intent}', but the '{agent_name}' is not available yet.",
                agent_name="brain.router",
                action="route",
                data={"intent": intent.intent, "agent_name": agent_name},
            )
            self.events.emit("agent.unavailable", source="brain.router", message=result.message, data=result.data)
            return result

        self.events.emit("agent.selected", source="brain.router", data={"agent_name": agent_name, "intent": intent.intent})
        context: dict[str, Any] = {
            "intent": intent,
            "registry": self.registry,
            "events": self.events,
            "llm_provider": self.llm_provider,
            "config": self.config,
            "timing": timing,
            "stream_callback": stream_callback,
            "short_term_memory": self.short_term_memory,
            "long_term_memory": self.long_term_memory,
            "ability_registry": self.ability_registry,
            "ability_selection": ability_selection,
        }

        try:
            self._mark(timing, "agent.handle_start", agent_name=agent_name)
            result = agent.handle(command, context=context)
            self._mark(timing, "agent.handle_finished", agent_name=agent_name, success=result.success)
        except Exception as exc:  # Keep runtime safe while agents are young.
            self._mark(timing, "agent.handle_failed", agent_name=agent_name, error=str(exc))
            result = JarvisResult.fail(
                f"{agent_name} failed while handling the command.",
                agent_name=agent_name,
                action="handle",
                errors=[str(exc)],
                data={"intent": intent.intent},
            )

        result.data.setdefault("intent", intent.intent)
        result.data.setdefault("intent_confidence", intent.confidence)
        result.data.setdefault("selected_agent", agent_name)
        if ability_selection is not None:
            result.data.setdefault("ability_selection", ability_selection.to_dict())
        for event in result.events:
            self.events.emit(event.event_type, source=event.source, message=event.message, data=event.data)
        self.events.emit("agent.finished", source=agent_name, message=result.message, data=result.data)
        self.events.emit("jarvis.response_ready", source="brain.router", message=result.message, data={"success": result.success})
        self._mark(timing, "brain.response_ready", success=result.success)
        return result

    def _mark(self, timing: Any | None, name: str, **data: Any) -> None:
        if timing is not None and hasattr(timing, "mark"):
            timing.mark(name, **data)
