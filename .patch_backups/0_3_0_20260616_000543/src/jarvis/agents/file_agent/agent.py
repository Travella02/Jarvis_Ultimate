"""File Agent implementation with safe read-only project abilities."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from jarvis.core.result import JarvisEvent, JarvisResult
from jarvis.tools.shared.safe_files import project_status, search_project_files


class Agent:
    name = "file_agent"

    def __init__(self, *, manifest: dict[str, Any] | None = None, registry: Any | None = None) -> None:
        self.manifest = manifest or {}
        self.registry = registry

    def handle(self, command: str, context: dict[str, Any] | None = None) -> JarvisResult:
        context = context or {}
        command_text = str(command or "").strip()
        text = command_text.lower()
        config = context.get("config")
        project_root = Path(getattr(config, "project_root", Path.cwd())) if config is not None else Path.cwd()

        if _looks_like_write_request(text):
            return JarvisResult.confirmation(
                "That file action could change your project, sir. I need confirmation before doing file writes.",
                confirmation_prompt="Confirm the exact file operation you want Jarvis to run.",
                agent_name=self.name,
                action="file_write_confirmation_required",
                data={"command": command_text, "risk_level": "confirm"},
            )

        query = _extract_search_query(command_text)
        if query:
            matches = search_project_files(project_root, query, max_results=12)
            if matches:
                preview = ", ".join(match.path for match in matches[:5])
                if len(matches) > 5:
                    preview += f", and {len(matches) - 5} more"
                message = f"I found {len(matches)} project file match(es) for '{query}': {preview}."
            else:
                message = f"I did not find any project file names matching '{query}', sir."
            return JarvisResult.ok(
                message,
                agent_name=self.name,
                action="search_project_files",
                data={"implemented": True, "query": query, "matches": [match.to_dict() for match in matches]},
                events=[_action_card_event("Project File Search", "complete", query, message, self.name)],
            )


        if "project status" in text or "jarvis project status" in text or "project files" in text:
            status = project_status(project_root)
            message = (
                f"Jarvis project status: source {'found' if status['src_exists'] else 'missing'}, "
                f"app shell {'found' if status['app_shell_exists'] else 'missing'}, "
                f"{status['agent_count']} agents, and {status['test_file_count']} test files."
            )
            return JarvisResult.ok(
                message,
                agent_name=self.name,
                action="project_status",
                data={"implemented": True, "project_status": status},
                events=[_action_card_event("Project Status", "complete", "Jarvis_Ultimate", message, self.name)],
            )

        return JarvisResult.ok(
            "File Agent is online with safe project status and filename search. Try: 'Jarvis, search project files for renderer' or 'Jarvis, project status.'",
            agent_name=self.name,
            action="file_agent_help",
            data={"implemented": True, "safe_modes": ["project_status", "search_project_files"]},
        )


def _looks_like_write_request(text: str) -> bool:
    return any(phrase in text for phrase in ["delete", "remove", "move", "rename", "write", "overwrite", "edit file"])


def _extract_search_query(command: str) -> str:
    text = str(command or "").strip()
    patterns = [
        r"search project files for\s+(.+)$",
        r"search files for\s+(.+)$",
        r"find file\s+(.+)$",
        r"look for file\s+(.+)$",
        r"find\s+(.+)\s+in project files$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.group(1).strip().strip(".?!\"")
    return ""


def _action_card_event(title: str, status: str, target: str, message: str, agent_name: str) -> JarvisEvent:
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
