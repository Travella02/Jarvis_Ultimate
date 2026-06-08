"""Jarvis brain router."""

from __future__ import annotations

from typing import Any

from jarvis.brain.intent_classifier import IntentClassifier
from jarvis.core.events import EventBus
from jarvis.core.registry import AgentRegistry
from jarvis.core.result import JarvisResult


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
    ) -> None:
        self.registry = registry
        self.events = events or EventBus()
        self.classifier = classifier or IntentClassifier()
        self.llm_provider = llm_provider

    def handle(self, command: str) -> JarvisResult:
        self.events.emit("user.command.received", source="brain.router", message=command)
        self.events.emit("brain.routing_started", source="brain.router")

        intent = self.classifier.classify(command)
        agent_name = INTENT_AGENT_MAP.get(intent.intent, "conversation_agent")
        self.events.emit(
            "brain.intent_classified",
            source="brain.router",
            data={"intent": intent.intent, "confidence": intent.confidence, "reason": intent.reason, "agent_name": agent_name},
        )

        agent = self.registry.get_agent(agent_name)
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
        }

        try:
            result = agent.handle(command, context=context)
        except Exception as exc:  # Keep runtime safe while agents are young.
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
        self.events.emit("agent.finished", source=agent_name, message=result.message, data=result.data)
        self.events.emit("jarvis.response_ready", source="brain.router", message=result.message, data={"success": result.success})
        return result
