"""App Agent implementation."""

from __future__ import annotations

from pathlib import Path
import os
import re
import sys
from typing import Any

from jarvis.core.result import JarvisEvent, JarvisResult
from jarvis.tools.shared.app_discovery import (
    AppAliasStore,
    clean_app_target,
    close_app_match,
    launch_app_match,
    resolve_app_target,
)
from jarvis.tools.shared.process_tools import clean_launch_target, looks_like_url_or_domain, normalize_url, open_website


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

        dry_run = _dry_run_requested(context)
        alias_request = _parse_alias_teach_command(command_text)
        if alias_request is not None:
            alias, target = alias_request
            return self._handle_alias_teach(alias, target, command_text, project_root=project_root, dry_run=dry_run)
        if _is_close_command(command_text):
            return self._handle_close(command_text, project_root=project_root, dry_run=dry_run)
        return self._handle_open(command_text, project_root=project_root, dry_run=dry_run)

    def _handle_alias_teach(self, alias: str, target: str, command_text: str, *, project_root: Path, dry_run: bool = False) -> JarvisResult:
        alias = str(alias or "").strip().strip(".?!")
        target = str(target or "").strip().strip(".?!")
        if not alias or not target:
            return JarvisResult.fail(
                "Tell me the nickname and the app you want it to open, sir.",
                agent_name=self.name,
                action="learn_app_alias",
                data={"command": command_text, "alias": alias, "target": target},
            )

        match = resolve_app_target(target, project_root, dry_run=dry_run)
        if match.candidate is None:
            return JarvisResult.fail(
                f"I could not find {target} yet, so I cannot learn that app name, sir.",
                agent_name=self.name,
                action="learn_app_alias",
                errors=["app_not_found"],
                data={"command": command_text, "alias": alias, "target": target, "app_match": match.to_dict()},
            )

        AppAliasStore(project_root).save_alias(alias, match.candidate, source="manual_teach")
        message = f"Understood, sir. When you say {alias}, I will use {match.candidate.name}."
        event = _action_card_event(
            title="Learned App Alias",
            status="complete",
            target=match.candidate.name,
            message=message,
            agent_name=self.name,
        )
        return JarvisResult.ok(
            message,
            agent_name=self.name,
            action="learn_app_alias",
            data={"command": command_text, "alias": alias, "target": target, "app_match": match.to_dict(), "implemented": True},
            events=[event],
        )

    def _handle_open(self, command_text: str, *, project_root: Path, dry_run: bool = False) -> JarvisResult:
        target = clean_app_target(command_text)
        lower_target = target.lower()

        if not target:
            return JarvisResult.fail(
                "Tell me which app or website you want me to open, sir.",
                agent_name=self.name,
                action="open_target",
                data={"command": command_text},
            )

        if "project folder" in lower_target or "jarvis folder" in lower_target:
            # Keep project folder opening deterministic and fast.
            match = resolve_app_target("file explorer", project_root, dry_run=dry_run)
            launch_result = launch_app_match(match, project_root=project_root, alias_to_learn=target, dry_run=dry_run)
            action_target_data = match.to_dict()
        elif _target_is_website(lower_target):
            website_target = _clean_website_target(target)
            launch_result = open_website(website_target, dry_run=dry_run)
            action_target_data = {"query": target, "type": "website", "url": normalize_url(website_target)}
        else:
            match = resolve_app_target(target, project_root, dry_run=dry_run)
            launch_result = launch_app_match(match, project_root=project_root, alias_to_learn=target, dry_run=dry_run)
            action_target_data = match.to_dict()

        result_data = {
            "command": command_text,
            "target": launch_result.target,
            "requested_target": target,
            "launch_type": launch_result.launch_type,
            "launcher": launch_result.to_dict(),
            "app_match": action_target_data,
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

    def _handle_close(self, command_text: str, *, project_root: Path, dry_run: bool = False) -> JarvisResult:
        target = clean_app_target(command_text, close=True)
        if not target:
            return JarvisResult.fail(
                "Tell me which app you want me to close, sir.",
                agent_name=self.name,
                action="close_target",
                data={"command": command_text},
            )

        match = resolve_app_target(target, project_root, dry_run=dry_run)
        close_result = close_app_match(match, project_root=project_root, alias_to_learn=target, dry_run=dry_run)
        result_data = {
            "command": command_text,
            "target": close_result.target,
            "requested_target": target,
            "launch_type": close_result.launch_type,
            "closer": close_result.to_dict(),
            "app_match": match.to_dict(),
            "implemented": True,
        }
        event = _action_card_event(
            title="Closing Application",
            status="complete" if close_result.success else "failed",
            target=close_result.target,
            message=close_result.message,
            agent_name=self.name,
        )
        if close_result.success:
            return JarvisResult.ok(
                close_result.message,
                agent_name=self.name,
                action="close_target",
                data=result_data,
                events=[event],
            )
        return JarvisResult.fail(
            close_result.message,
            agent_name=self.name,
            action="close_target",
            errors=close_result.errors or [close_result.message],
            data=result_data,
        )


def _dry_run_requested(context: dict[str, Any]) -> bool:
    """Return True when app actions should resolve but not touch the OS.

    Unit tests can pass ``dry_run=True`` so app-discovery tests never open or
    close real programs on the developer machine.  The unittest/pytest command
    guard is intentionally automatic because the full test suite should never
    launch Notepad, Chrome, Calculator, VS Code, or any other real app by
    accident.  Real Jarvis sessions launched through scripts/start_jarvis_app.py
    are not affected.
    """

    if _truthy(context.get("allow_os_launch_during_tests")) or _truthy(os.environ.get("JARVIS_ALLOW_OS_LAUNCH_DURING_TESTS")):
        return _truthy(context.get("dry_run", False))
    return (
        _truthy(context.get("dry_run", False))
        or _truthy(os.environ.get("JARVIS_APP_AGENT_DRY_RUN"))
        or _running_under_test_process()
    )


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _running_under_test_process() -> bool:
    argv = " ".join(str(part).lower() for part in sys.argv)
    return "unittest" in argv or "pytest" in argv


def _parse_alias_teach_command(command: str) -> tuple[str, str] | None:
    text = str(command or "").strip().strip(".?!")
    patterns = [
        r"^(?:jarvis[, ]+)?(?:please\s+)?(?:remember|learn)\s+(?:that\s+)?when\s+i\s+say\s+['\"]?(?P<alias>[^'\",]+)['\"]?\s*,?\s*(?:open|launch|start)\s+(?P<target>.+)$",
        r"^(?:jarvis[, ]+)?(?:please\s+)?when\s+i\s+say\s+['\"]?(?P<alias>[^'\",]+)['\"]?\s*,?\s*(?:open|launch|start)\s+(?P<target>.+)$",
        r"^(?:jarvis[, ]+)?(?:please\s+)?(?:remember|learn)\s+(?:that\s+)?['\"]?(?P<alias>[^'\",]+)['\"]?\s+means\s+(?P<target>.+)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, text, flags=re.IGNORECASE)
        if match:
            alias = " ".join(match.group("alias").split())
            target = " ".join(match.group("target").split())
            return alias, target
    return None


def _is_close_command(command: str) -> bool:
    text = str(command or "").strip().lower()
    return bool(re.match(r"^(?:jarvis[, ]+)?(?:please\s+)?(?:close|quit|exit|shut\s+down|stop)\b", text))


def _target_is_website(target: str) -> bool:
    text = str(target or "").strip().lower()
    if text.startswith(("http://", "https://")):
        return True
    if re.search(r"\b(website|web site|site|url|webpage|web page)\b", text):
        return True
    # Domains should still open as websites. Bare words such as "google" now go
    # through the app resolver so aliases like Google -> Chrome can be learned.
    return bool(looks_like_url_or_domain(text))


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


def _clean_website_target(target: str) -> str:
    text = re.sub(r"\b(website|web site|site|url|webpage|web page)\b", "", str(target or ""), flags=re.IGNORECASE)
    return " ".join(text.split()) or target
