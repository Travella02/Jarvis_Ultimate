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
    region: str = "workspace"
    order: int = 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "panel_id": self.panel_id,
            "title": self.title,
            "panel_type": self.panel_type,
            "description": self.description,
            "icon": self.icon,
            "default_open": self.default_open,
            "payload": dict(self.payload),
            "region": self.region,
            "order": self.order,
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
        return sorted(self._panels.values(), key=lambda spec: (spec.region, spec.order, spec.panel_id))

    def openable(self) -> list[UIPanelSpec]:
        return self.all()

    def by_region(self, region: str) -> list[UIPanelSpec]:
        return [spec for spec in self.all() if spec.region == region]


def create_default_panel_registry() -> UIPanelRegistry:
    """Create the default panel set for Jarvis's first desktop shell."""

    registry = UIPanelRegistry()
    for spec in [
        UIPanelSpec("avatar", "Avatar", "avatar", "Jarvis visual body/state display.", "◉", True, region="left", order=10),
        UIPanelSpec("status", "Status", "status", "Runtime, voice, memory, and provider state.", "◆", True, region="left", order=20),
        UIPanelSpec("chat", "Chat", "chat", "Conversation stream and typed commands.", "💬", True, region="center", order=10),
        UIPanelSpec("workspace", "Workspace", "workspace", "Future dynamic cards: web, reminders, images, files, and tools.", "▣", True, region="right", order=10),
        UIPanelSpec("events", "Event Log", "events", "Recent Jarvis events for debugging and UI state.", "☰", True, region="right", order=20),
        UIPanelSpec("agents", "Agents", "agents", "Registered agents and their status.", "☷", False, region="workspace", order=30),
        UIPanelSpec("debug", "Debug", "debug", "Timing/debug output and runtime notes.", "⚙", False, region="workspace", order=40),
        UIPanelSpec("reminders", "Reminders", "cards", "Reminder cards Jarvis can create or manage.", "⏰", False, region="workspace", order=50),
        UIPanelSpec("web_results", "Web Results", "results", "Search results and web summaries.", "◎", False, region="workspace", order=60),
        UIPanelSpec("generated_images", "Generated Images", "image_grid", "Images created or edited by Jarvis.", "▧", False, region="workspace", order=70),
        UIPanelSpec("file_results", "Files", "file_list", "Files Jarvis found or created.", "▤", False, region="workspace", order=80),
        UIPanelSpec("screen_context", "Screen Context", "screen", "Screen capture, active window, and OCR context.", "▣", False, region="workspace", order=90),
        UIPanelSpec("agent_dashboard", "Agent Dashboard", "agents", "Detailed agent activity and routing state.", "☷", False, region="workspace", order=100),
    ]:
        registry.register(spec)
    return registry
