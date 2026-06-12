"""Ability registry and lightweight command selection for Jarvis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from jarvis.abilities.permissions import AbilityPermissionPolicy
from jarvis.core.registry import AgentRegistry


@dataclass(slots=True)
class AbilityRecord:
    """Metadata for one callable Jarvis ability owned by an agent."""

    name: str
    display_name: str
    agent_name: str
    description: str
    intent: str = "general_chat"
    permissions: list[str] = field(default_factory=list)
    risk_level: str = "safe"
    triggers: list[str] = field(default_factory=list)
    examples: list[str] = field(default_factory=list)
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "agent_name": self.agent_name,
            "description": self.description,
            "intent": self.intent,
            "permissions": list(self.permissions),
            "risk_level": self.risk_level,
            "triggers": list(self.triggers),
            "examples": list(self.examples),
            "enabled": self.enabled,
        }


@dataclass(slots=True)
class AbilitySelection:
    """Best-effort selected ability for a command."""

    ability: AbilityRecord | None
    confidence: float = 0.0
    reason: str = "No ability selected."

    def to_dict(self) -> dict[str, Any]:
        return {
            "ability": self.ability.to_dict() if self.ability else None,
            "confidence": self.confidence,
            "reason": self.reason,
        }


class AbilityRegistry:
    """Central inventory of Jarvis abilities.

    Agents are still the specialist owners. The ability registry is the layer
    Jarvis uses to advertise and select concrete capabilities inside those
    agents.
    """

    def __init__(self, *, permission_policy: AbilityPermissionPolicy | None = None) -> None:
        self._records: dict[str, AbilityRecord] = {}
        self.permission_policy = permission_policy or AbilityPermissionPolicy()

    def register(self, record: AbilityRecord) -> None:
        self._records[record.name] = record

    def get(self, name: str) -> AbilityRecord | None:
        return self._records.get(name)

    def all(self, *, enabled_only: bool = True) -> list[AbilityRecord]:
        records = list(self._records.values())
        if enabled_only:
            records = [record for record in records if record.enabled]
        return sorted(records, key=lambda record: (record.agent_name, record.name))

    def names(self, *, enabled_only: bool = True) -> list[str]:
        return [record.name for record in self.all(enabled_only=enabled_only)]

    def count(self, *, enabled_only: bool = True) -> int:
        return len(self.all(enabled_only=enabled_only))

    def to_list(self, *, enabled_only: bool = True) -> list[dict[str, Any]]:
        return [record.to_dict() for record in self.all(enabled_only=enabled_only)]

    def load_from_agent_registry(self, agent_registry: AgentRegistry) -> None:
        """Build ability records from enabled agent manifests plus curated tool metadata."""

        self._records.clear()
        for agent in agent_registry.enabled_records():
            for tool_name in agent.tools:
                ability = curated_ability_for_tool(str(tool_name), agent_name=agent.name, intent=agent.intents[0] if agent.intents else "general_chat", permissions=agent.permissions)
                self.register(ability)

    def select_for_command(self, command: str, *, intent: str | None = None) -> AbilitySelection:
        """Select the best ability using safe deterministic trigger matching.

        Later this can be LLM-assisted. For now, deterministic matching keeps the
        framework predictable and testable while agents are still young.
        """

        text = " ".join(str(command or "").lower().split())
        if not text:
            return AbilitySelection(None, 0.0, "No command text was provided.")

        candidates = [record for record in self.all(enabled_only=True) if intent is None or record.intent == intent]
        best: tuple[float, AbilityRecord, str] | None = None
        for record in candidates:
            score = 0.0
            reason = ""
            for trigger in record.triggers:
                trigger_text = str(trigger).lower().strip()
                if not trigger_text:
                    continue
                if trigger_text == text:
                    score = max(score, 1.0)
                    reason = f"Exact trigger matched: {trigger_text}"
                elif trigger_text in text:
                    trigger_score = min(0.92, 0.55 + (len(trigger_text) / max(len(text), 1)) * 0.35)
                    if trigger_score > score:
                        score = trigger_score
                        reason = f"Trigger phrase matched: {trigger_text}"
            if score and (best is None or score > best[0]):
                best = (score, record, reason)

        if best is None:
            return AbilitySelection(None, 0.0, f"No ability trigger matched for intent {intent or 'unknown'}.")
        return AbilitySelection(best[1], round(best[0], 3), best[2])

    def permission_decision(self, ability_name: str):
        record = self.get(ability_name)
        if record is None:
            return self.permission_policy.evaluate(ability_name=ability_name, risk_level="blocked", permissions=["dangerous"])
        return self.permission_policy.evaluate(ability_name=record.name, risk_level=record.risk_level, permissions=record.permissions)


def curated_ability_for_tool(tool_name: str, *, agent_name: str, intent: str, permissions: Iterable[str] = ()) -> AbilityRecord:
    """Return curated ability metadata for known tools, with safe fallbacks."""

    tool = str(tool_name).strip()
    permission_list = [str(permission) for permission in permissions]
    curated: dict[str, dict[str, Any]] = {
        "launcher": {
            "display_name": "Open Apps and Websites",
            "description": "Open safe known desktop apps, project folders, and websites.",
            "risk_level": "safe",
            "triggers": ["open", "launch", "start", "open app", "open website", "open project folder"],
            "examples": ["Jarvis, open VS Code", "Jarvis, open the project folder"],
            "permissions": ["app_control"],
        },
        "process_checker": {
            "display_name": "Check Running Processes",
            "description": "Report basic process/app status without changing anything.",
            "risk_level": "read_only",
            "triggers": ["is running", "check app", "process status"],
            "examples": ["Jarvis, is Chrome running?"],
        },
        "window_controller": {
            "display_name": "Window Control",
            "description": "Future window switching and focus control.",
            "risk_level": "confirm",
            "triggers": ["switch to", "focus window", "close window"],
            "examples": ["Jarvis, switch to VS Code"],
        },
        "file_search": {
            "display_name": "Search Project Files",
            "description": "Search filenames in the Jarvis project safely.",
            "risk_level": "read_only",
            "triggers": ["search project files", "find file", "look for file", "project status", "jarvis project status"],
            "examples": ["Jarvis, search project files for renderer"],
            "permissions": ["file_read"],
        },
        "file_ops": {
            "display_name": "File Operations",
            "description": "Future safe file organization actions; write operations require confirmation.",
            "risk_level": "confirm",
            "triggers": ["move file", "rename file", "organize files"],
            "examples": ["Jarvis, organize these screenshots"],
            "permissions": ["file_write"],
        },
        "storage_usage": {
            "display_name": "Project Storage Status",
            "description": "Report safe storage and project structure information.",
            "risk_level": "read_only",
            "triggers": ["storage", "project status", "jarvis status", "project files"],
            "examples": ["Jarvis, what is the project status?"],
            "permissions": ["file_read"],
        },
        "weather_lookup": {
            "display_name": "Weather Lookup",
            "description": "Future current weather and forecast lookup.",
            "risk_level": "external",
            "triggers": ["weather", "forecast", "temperature"],
            "examples": ["Jarvis, what is the weather?"],
            "permissions": ["network"],
        },
        "llm_chat": {
            "display_name": "Conversation",
            "description": "Normal Jarvis conversation through the configured LLM.",
            "risk_level": "safe",
            "triggers": ["chat", "answer", "explain", "tell me"],
            "examples": ["Jarvis, explain what an API is"],
            "permissions": [],
        },
    }
    meta = curated.get(tool, {})
    return AbilityRecord(
        name=f"{agent_name}.{tool}",
        display_name=str(meta.get("display_name") or tool.replace("_", " ").title()),
        agent_name=agent_name,
        description=str(meta.get("description") or f"{tool.replace('_', ' ').title()} ability owned by {agent_name}."),
        intent=intent,
        permissions=list(meta.get("permissions") or permission_list),
        risk_level=str(meta.get("risk_level") or "safe"),
        triggers=list(meta.get("triggers") or [tool.replace("_", " ")]),
        examples=list(meta.get("examples") or []),
        enabled=True,
    )
