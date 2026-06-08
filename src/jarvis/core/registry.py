"""Agent registry for Jarvis 3."""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from typing import Any, Protocol

from jarvis.core.result import JarvisResult


class AgentProtocol(Protocol):
    name: str

    def handle(self, command: str, context: dict[str, Any] | None = None) -> JarvisResult:
        ...


@dataclass(slots=True)
class AgentRecord:
    name: str
    display_name: str
    description: str
    intents: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    enabled: bool = True
    module_name: str | None = None
    agent: AgentProtocol | None = None

    @classmethod
    def from_manifest(cls, manifest: dict[str, Any], *, module_name: str | None = None, agent: AgentProtocol | None = None) -> "AgentRecord":
        return cls(
            name=str(manifest.get("name", module_name or "unknown_agent")),
            display_name=str(manifest.get("display_name", manifest.get("name", "Unknown Agent"))),
            description=str(manifest.get("description", "")),
            intents=list(manifest.get("intents", [])),
            permissions=list(manifest.get("permissions", [])),
            tools=list(manifest.get("tools", [])),
            enabled=bool(manifest.get("enabled_by_default", True)),
            module_name=module_name,
            agent=agent,
        )


class PlaceholderAgent:
    """Safe fallback when an agent has a manifest but no implementation yet."""

    def __init__(self, name: str, display_name: str, description: str = "") -> None:
        self.name = name
        self.display_name = display_name
        self.description = description

    def handle(self, command: str, context: dict[str, Any] | None = None) -> JarvisResult:
        return JarvisResult.ok(
            f"{self.display_name} is registered, but its real tools are not implemented yet.",
            agent_name=self.name,
            action="placeholder_response",
            data={"command": command, "implemented": False},
        )


class AgentRegistry:
    """Keeps track of every available Jarvis agent."""

    def __init__(self) -> None:
        self._records: dict[str, AgentRecord] = {}

    def register(self, record: AgentRecord) -> None:
        self._records[record.name] = record

    def register_from_manifest(self, manifest: dict[str, Any], *, module_name: str | None = None, agent: AgentProtocol | None = None) -> AgentRecord:
        record = AgentRecord.from_manifest(manifest, module_name=module_name, agent=agent)
        if record.agent is None:
            record.agent = PlaceholderAgent(record.name, record.display_name, record.description)
        self.register(record)
        return record

    def get(self, name: str) -> AgentRecord | None:
        return self._records.get(name)

    def get_agent(self, name: str) -> AgentProtocol | None:
        record = self.get(name)
        if record is None or not record.enabled:
            return None
        return record.agent

    def names(self, *, enabled_only: bool = True) -> list[str]:
        records = self.enabled_records() if enabled_only else list(self._records.values())
        return sorted(record.name for record in records)

    def enabled_records(self) -> list[AgentRecord]:
        return [record for record in self._records.values() if record.enabled]

    def all_records(self) -> list[AgentRecord]:
        return list(self._records.values())

    def load_builtin_agents(self) -> None:
        """Discover and register modules under jarvis.agents."""
        agents_package = importlib.import_module("jarvis.agents")
        for module_info in pkgutil.iter_modules(agents_package.__path__):
            if module_info.name.startswith("_"):
                continue
            package_name = f"jarvis.agents.{module_info.name}"
            manifest = self._load_manifest(package_name)
            if manifest is None:
                continue
            agent = self._load_agent(package_name, manifest)
            self.register_from_manifest(manifest, module_name=package_name, agent=agent)

    def _load_manifest(self, package_name: str) -> dict[str, Any] | None:
        try:
            manifest_module = importlib.import_module(f"{package_name}.manifest")
        except ModuleNotFoundError:
            return None
        manifest = getattr(manifest_module, "MANIFEST", None)
        return manifest if isinstance(manifest, dict) else None

    def _load_agent(self, package_name: str, manifest: dict[str, Any]) -> AgentProtocol | None:
        try:
            agent_module = importlib.import_module(f"{package_name}.agent")
        except ModuleNotFoundError:
            return None
        agent_cls = getattr(agent_module, "Agent", None)
        if agent_cls is None:
            return None
        try:
            return agent_cls(manifest=manifest, registry=self)
        except TypeError:
            try:
                return agent_cls(manifest=manifest)
            except TypeError:
                return agent_cls()
