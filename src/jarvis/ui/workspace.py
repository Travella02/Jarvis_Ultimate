"""Framework-neutral workspace state for Jarvis's desktop interface."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

from jarvis.core.result import JarvisEvent
from jarvis.memory.secure_vault import redact_sensitive_text
from jarvis.ui.avatar_state import AvatarState
from jarvis.ui.panels import UIPanelRegistry, create_default_panel_registry
from jarvis.ui.ui_events import avatar_state_from_event


@dataclass(slots=True)
class WorkspacePanelState:
    panel_id: str
    title: str
    panel_type: str = "text"
    is_open: bool = False
    payload: dict[str, Any] = field(default_factory=dict)
    region: str = "workspace"
    order: int = 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "panel_id": self.panel_id,
            "title": self.title,
            "panel_type": self.panel_type,
            "is_open": self.is_open,
            "payload": dict(self.payload),
            "region": self.region,
            "order": self.order,
        }


class UIWorkspaceState:
    """Current UI/body state shared by desktop, web, and future clients."""

    def __init__(self, *, panel_registry: UIPanelRegistry | None = None, event_limit: int = 250) -> None:
        self.avatar = AvatarState(state="sleeping", expression="calm", message="Waiting for wake phrase.")
        self.panel_registry = panel_registry or create_default_panel_registry()
        self.panels: dict[str, WorkspacePanelState] = {}
        self.events: deque[JarvisEvent] = deque(maxlen=event_limit)
        self.chat_messages: deque[dict[str, str]] = deque(maxlen=200)
        self.agent_status: dict[str, str] = {}
        self.workspace_cards: deque[dict[str, Any]] = deque(maxlen=50)
        self.notices: deque[str] = deque(maxlen=25)
        self._hydrate_default_panels()

    def _hydrate_default_panels(self) -> None:
        for spec in self.panel_registry.all():
            self.panels[spec.panel_id] = WorkspacePanelState(
                panel_id=spec.panel_id,
                title=spec.title,
                panel_type=spec.panel_type,
                is_open=spec.default_open,
                payload=dict(spec.payload),
                region=spec.region,
                order=spec.order,
            )

    def add_chat_message(self, role: str, text: str) -> None:
        safe_text = redact_sensitive_text(str(text or ""), max_chars=max(len(str(text or "")), 120))
        self.chat_messages.append({"role": role, "text": safe_text})

    def add_notice(self, message: str) -> None:
        if message:
            self.notices.append(message)

    def set_agent_status(self, agent_name: str, status: str) -> None:
        self.agent_status[agent_name] = status

    def open_panel(self, panel_id: str, *, title: str | None = None, panel_type: str = "text", payload: dict[str, Any] | None = None) -> WorkspacePanelState:
        panel = self.panels.get(panel_id)
        spec = self.panel_registry.get(panel_id)
        if panel is None:
            panel = WorkspacePanelState(
                panel_id=panel_id,
                title=title or (spec.title if spec else panel_id.replace("_", " ").title()),
                panel_type=panel_type if spec is None else spec.panel_type,
                is_open=True,
                payload=payload or {},
                region=spec.region if spec else "workspace",
                order=spec.order if spec else 100,
            )
            self.panels[panel_id] = panel
        panel.is_open = True
        if title:
            panel.title = title
        if payload is not None:
            panel.payload = payload
        return panel

    def close_panel(self, panel_id: str) -> None:
        panel = self.panels.get(panel_id)
        if panel is not None:
            panel.is_open = False

    def update_panel(self, panel_id: str, *, payload: dict[str, Any] | None = None) -> WorkspacePanelState:
        panel = self.open_panel(panel_id)
        if payload is not None:
            panel.payload.update(payload)
        return panel

    def panel_summaries(self) -> list[dict[str, Any]]:
        panels = sorted(self.panels.values(), key=lambda panel: (panel.region, panel.order, panel.panel_id))
        return [panel.to_dict() for panel in panels]

    def open_panels(self) -> list[WorkspacePanelState]:
        return [panel for panel in sorted(self.panels.values(), key=lambda panel: (panel.region, panel.order, panel.panel_id)) if panel.is_open]

    def add_workspace_card(self, card_type: str, title: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        card = {"type": card_type, "title": title, "payload": payload or {}}
        self.workspace_cards.append(card)
        self.open_panel("workspace")
        return card

    def apply_event(self, event: JarvisEvent) -> None:
        self.events.append(event)
        avatar_state = avatar_state_from_event(event.event_type)
        if avatar_state:
            expression = "alert" if avatar_state == "error" else None
            self.avatar.set_state(avatar_state, expression=expression, message=event.message)

        if event.event_type == "ui.avatar_state":
            state = str(event.data.get("state", "idle"))
            expression = str(event.data.get("expression", self.avatar.expression))
            message = str(event.data.get("message", event.message))
            self.avatar.set_state(state, expression=expression, message=message)
        elif event.event_type == "ui.open_panel":
            self.open_panel(
                str(event.data.get("panel_id", "workspace")),
                title=event.data.get("title"),
                payload=event.data.get("payload") if isinstance(event.data.get("payload"), dict) else {},
            )
        elif event.event_type == "ui.update_panel":
            payload = event.data.get("payload")
            self.update_panel(str(event.data.get("panel_id", "workspace")), payload=payload if isinstance(payload, dict) else {})
        elif event.event_type == "ui.close_panel":
            self.close_panel(str(event.data.get("panel_id", "workspace")))
        elif event.event_type == "ui.workspace_card":
            payload = event.data.get("payload")
            self.add_workspace_card(str(event.data.get("card_type", "card")), str(event.data.get("title", event.message or "Workspace Card")), payload if isinstance(payload, dict) else {})
        elif event.event_type.startswith("agent.") and event.source:
            self.set_agent_status(event.source, event.message or event.event_type)

    def snapshot(self) -> dict[str, Any]:
        return {
            "avatar": self.avatar.to_dict(),
            "panels": {key: panel.to_dict() for key, panel in sorted(self.panels.items())},
            "events": [event.to_dict() for event in list(self.events)],
            "chat_messages": list(self.chat_messages),
            "agent_status": dict(sorted(self.agent_status.items())),
            "workspace_cards": list(self.workspace_cards),
            "notices": list(self.notices),
        }
