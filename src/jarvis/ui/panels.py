"""Drop-in UI panel registry for Jarvis's future visual workspace.

The desktop UI should not hard-code every future feature. New tools/agents can
register a panel spec and later emit ui.open_panel/ui.update_panel events. This
keeps the UI extensible like the agent/provider architecture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class UIPanelSpec:
    """Description of a panel Jarvis can open in his interface."""

    panel_id: str
    title: str
    panel_type: str = "text"
    description: str = ""
    icon: str = ""
    default_open: bool = False
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "panel_id": self.panel_id,
            "title": self.title,
            "panel_type": self.panel_type,
            "description": self.description,
            "icon": self.icon,
            "default_open": self.default_open,
            "payload": dict(self.payload),
        }


class UIPanelRegistry:
    """Registry for panels that can be added without rewriting the UI shell."""

    def __init__(self) -> None:
        self._panels: dict[str, UIPanelSpec] = {}

    def register(self, spec: UIPanelSpec) -> UIPanelSpec:
        if not spec.panel_id.strip():
            raise ValueError("panel_id is required")
        self._panels[spec.panel_id] = spec
        return spec

    def get(self, panel_id: str) -> UIPanelSpec | None:
        return self._panels.get(panel_id)

    def names(self) -> list[str]:
        return sorted(self._panels)

    def all(self) -> list[UIPanelSpec]:
        return [self._panels[name] for name in self.names()]

    def openable(self) -> list[UIPanelSpec]:
        return self.all()


def create_default_panel_registry() -> UIPanelRegistry:
    """Create the default panel set for Jarvis's first desktop shell."""

    registry = UIPanelRegistry()
    for spec in [
        UIPanelSpec("chat", "Chat", "chat", "Conversation stream and typed commands.", "💬", True),
        UIPanelSpec("avatar", "Avatar", "avatar", "Jarvis visual body/state display.", "◉", True),
        UIPanelSpec("status", "Status", "status", "Runtime, voice, memory, and provider state.", "◆", True),
        UIPanelSpec("agents", "Agents", "agents", "Registered agents and their status.", "☷", True),
        UIPanelSpec("events", "Event Log", "events", "Recent Jarvis events for debugging and UI state.", "☰", True),
        UIPanelSpec("workspace", "Workspace", "workspace", "Future dynamic cards: web, reminders, images, files, and tools.", "▣", True),
        UIPanelSpec("debug", "Debug", "debug", "Timing/debug output and runtime notes.", "⚙", False),
    ]:
        registry.register(spec)
    return registry
