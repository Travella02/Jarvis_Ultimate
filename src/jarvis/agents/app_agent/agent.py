"""App Agent implementation."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from jarvis.core.result import JarvisEvent, JarvisResult
from jarvis.tools.shared.process_tools import clean_launch_target, looks_like_url_or_domain, launch_known_app, normalize_app_name, open_website


class Agent:
    name = "app_agent"

    def __init__(self, *, manifest: dict[str, Any] | None = None, registry: Any | None = None) -> None:
        self.manifest = manifest or {}
        self.registry = registry

    def handle(self, command: str, context: dict[str, Any] | None = None) -> JarvisResult:
        context = context or {}
        config = context.get("config")
        project_root = Path(getattr(config, "project_root", Path.cwd())) if config is not None else Path.cwd()
        command_text = str(command or "").strip()
        target = clean_launch_target(command_text)
        lower_target = target.lower()

        if not target:
            return JarvisResult.fail(
                "Tell me which app or website you want me to open, sir.",
                agent_name=self.name,
                action="open_target",
                data={"command": command_text},
            )

        if "project folder" in lower_target or "jarvis folder" in lower_target:
            launch_result = launch_known_app("file explorer", project_root=project_root)
        elif _target_is_website(lower_target):
            launch_result = open_website(target)
        else:
            launch_result = launch_known_app(normalize_app_name(target), project_root=project_root)

        result_data = {
            "command": command_text,
            "target": launch_result.target,
            "launch_type": launch_result.launch_type,
            "launcher": launch_result.to_dict(),
            "implemented": True,
        }
        event = _action_card_event(
            title="Opening " + ("Website" if launch_result.launch_type == "website" else "Application"),
            status="complete" if launch_result.success else "failed",
            target=launch_result.target,
            message=launch_result.message,
            agent_name=self.name,
        )
        if launch_result.success:
            return JarvisResult.ok(
                launch_result.message,
                agent_name=self.name,
                action="open_target",
                data=result_data,
                events=[event],
            )
        return JarvisResult.fail(
            launch_result.message,
            agent_name=self.name,
            action="open_target",
            errors=launch_result.errors or [launch_result.message],
            data=result_data,
        )


def _target_is_website(target: str) -> bool:
    if target in {"google", "youtube", "github", "chatgpt", "openai", "spotify"}:
        return True
    if target.startswith(("http://", "https://")):
        return True
    return bool(looks_like_url_or_domain(target)) or bool(re.search(r"\bwebsite\b|\bsite\b", target))


def _action_card_event(*, title: str, status: str, target: str, message: str, agent_name: str) -> JarvisEvent:
    return JarvisEvent(
        event_type="ui.workspace_card",
        source=agent_name,
        message=message,
        data={
            "card_type": "ability_action",
            "title": title,
            "payload": {
                "status": status,
                "target": target,
                "message": message,
                "agent": agent_name,
            },
        },
    )
