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
    focus_app_match,
    launch_app_match,
    normalize_query,
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
        alias_request = _parse_alias_management_command(command_text)
        if alias_request is not None:
            return self._handle_alias_management(alias_request, command_text, project_root=project_root, dry_run=dry_run)
        if _is_close_command(command_text):
            return self._handle_close(command_text, project_root=project_root, dry_run=dry_run)
        if _is_focus_command(command_text):
            return self._handle_focus(command_text, project_root=project_root, dry_run=dry_run)
        return self._handle_open(command_text, project_root=project_root, dry_run=dry_run)

    def _handle_alias_management(self, request: dict[str, Any], command_text: str, *, project_root: Path, dry_run: bool = False) -> JarvisResult:
        action = str(request.get("action") or "")
        if action == "teach_aliases":
            return self._handle_alias_teach(list(request.get("aliases") or []), str(request.get("target") or ""), command_text, project_root=project_root, dry_run=dry_run)
        if action == "set_role":
            return self._handle_set_role(str(request.get("role") or ""), str(request.get("target") or ""), command_text, project_root=project_root, dry_run=dry_run)
        if action == "forget_aliases":
            return self._handle_forget_aliases(list(request.get("aliases") or []), command_text, project_root=project_root)
        if action == "rename_alias":
            return self._handle_rename_alias(str(request.get("old_alias") or ""), str(request.get("new_alias") or ""), command_text, project_root=project_root)
        if action == "list_aliases":
            return self._handle_list_aliases(str(request.get("target") or ""), command_text, project_root=project_root)
        return JarvisResult.fail(
            "I understood that as an app-name request, sir, but I need the app name and nickname more clearly.",
            agent_name=self.name,
            action="manage_app_aliases",
            data={"command": command_text, "request": request},
        )

    def _handle_alias_teach(self, aliases: list[str], target: str, command_text: str, *, project_root: Path, dry_run: bool = False) -> JarvisResult:
        clean_aliases = _clean_alias_list(aliases)
        target = str(target or "").strip().strip(".?!")
        if not clean_aliases or not target:
            return JarvisResult.fail(
                "Tell me the nickname and the app you want it to open, sir.",
                agent_name=self.name,
                action="learn_app_alias",
                data={"command": command_text, "aliases": clean_aliases, "target": target},
            )

        match = resolve_app_target(target, project_root, dry_run=dry_run)
        if match.candidate is None:
            return JarvisResult.fail(
                f"I could not find {target} yet, so I cannot learn that app name, sir.",
                agent_name=self.name,
                action="learn_app_alias",
                errors=["app_not_found"],
                data={"command": command_text, "aliases": clean_aliases, "target": target, "app_match": match.to_dict()},
            )

        saved = AppAliasStore(project_root).save_aliases(clean_aliases, match.candidate, source="manual_teach")
        alias_text = _format_alias_list(saved)
        message = f"Understood, sir. {alias_text} will open {match.candidate.name}."
        event = _action_card_event(
            title="Learned App Aliases",
            status="complete",
            target=match.candidate.name,
            message=message,
            agent_name=self.name,
        )
        return JarvisResult.ok(
            message,
            agent_name=self.name,
            action="learn_app_alias",
            data={"command": command_text, "aliases": saved, "target": target, "app_match": match.to_dict(), "implemented": True},
            events=[event],
        )

    def _handle_set_role(self, role: str, target: str, command_text: str, *, project_root: Path, dry_run: bool = False) -> JarvisResult:
        role = normalize_query(role)
        target = str(target or "").strip().strip(".?!")
        if not role or not target:
            return JarvisResult.fail(
                "Tell me which app and what role it should be, sir.",
                agent_name=self.name,
                action="set_default_app_role",
                data={"command": command_text, "role": role, "target": target},
            )
        match = resolve_app_target(target, project_root, dry_run=dry_run)
        if match.candidate is None:
            return JarvisResult.fail(
                f"I could not find {target} yet, so I cannot make it your {role}, sir.",
                agent_name=self.name,
                action="set_default_app_role",
                errors=["app_not_found"],
                data={"command": command_text, "role": role, "target": target, "app_match": match.to_dict()},
            )
        aliases = AppAliasStore(project_root).save_role(role, match.candidate, source="manual_role")
        message = f"Understood, sir. I will use {match.candidate.name} as your {role}."
        event = _action_card_event(
            title="Set Default App Role",
            status="complete",
            target=match.candidate.name,
            message=message,
            agent_name=self.name,
        )
        return JarvisResult.ok(
            message,
            agent_name=self.name,
            action="set_default_app_role",
            data={"command": command_text, "role": role, "target": target, "aliases": aliases, "app_match": match.to_dict(), "implemented": True},
            events=[event],
        )

    def _handle_forget_aliases(self, aliases: list[str], command_text: str, *, project_root: Path) -> JarvisResult:
        clean_aliases = _clean_alias_list(aliases)
        if not clean_aliases:
            return JarvisResult.fail(
                "Tell me which app name you want me to forget, sir.",
                agent_name=self.name,
                action="forget_app_alias",
                data={"command": command_text},
            )
        store = AppAliasStore(project_root)
        removed = [alias for alias in clean_aliases if store.delete_alias(alias)]
        if not removed:
            return JarvisResult.fail(
                f"I do not have {_format_alias_list(clean_aliases)} saved as an app name yet, sir.",
                agent_name=self.name,
                action="forget_app_alias",
                errors=["alias_not_found"],
                data={"command": command_text, "aliases": clean_aliases},
            )
        message = f"Okay, sir. I forgot {_format_alias_list(removed)}."
        event = _action_card_event(
            title="Forgot App Alias",
            status="complete",
            target=", ".join(removed),
            message=message,
            agent_name=self.name,
        )
        return JarvisResult.ok(
            message,
            agent_name=self.name,
            action="forget_app_alias",
            data={"command": command_text, "aliases": clean_aliases, "removed": removed, "implemented": True},
            events=[event],
        )

    def _handle_rename_alias(self, old_alias: str, new_alias: str, command_text: str, *, project_root: Path) -> JarvisResult:
        old_clean = normalize_query(old_alias)
        new_clean = normalize_query(new_alias)
        if not old_clean or not new_clean:
            return JarvisResult.fail(
                "Tell me the old app name and the new one, sir.",
                agent_name=self.name,
                action="rename_app_alias",
                data={"command": command_text, "old_alias": old_alias, "new_alias": new_alias},
            )
        renamed = AppAliasStore(project_root).rename_alias(old_clean, new_clean)
        if not renamed:
            return JarvisResult.fail(
                f"I do not have {old_clean} saved as an app name yet, sir.",
                agent_name=self.name,
                action="rename_app_alias",
                errors=["alias_not_found"],
                data={"command": command_text, "old_alias": old_clean, "new_alias": new_clean},
            )
        message = f"Done, sir. I changed {old_clean} to {new_clean}."
        event = _action_card_event(
            title="Renamed App Alias",
            status="complete",
            target=f"{old_clean} → {new_clean}",
            message=message,
            agent_name=self.name,
        )
        return JarvisResult.ok(
            message,
            agent_name=self.name,
            action="rename_app_alias",
            data={"command": command_text, "old_alias": old_clean, "new_alias": new_clean, "implemented": True},
            events=[event],
        )

    def _handle_list_aliases(self, target: str, command_text: str, *, project_root: Path) -> JarvisResult:
        store = AppAliasStore(project_root)
        target = normalize_query(target)
        if target:
            aliases = store.aliases_for_target(target)
            message = f"For {target}, I remember {_format_alias_list(aliases)}, sir." if aliases else f"I do not have any custom names saved for {target} yet, sir."
            data = {"command": command_text, "target": target, "aliases": aliases, "implemented": True}
        else:
            groups = store.alias_groups()
            if not groups:
                message = "I do not have any custom app names saved yet, sir."
                data = {"command": command_text, "aliases": {}, "implemented": True}
            else:
                pieces = []
                data_groups: dict[str, Any] = {}
                for group in groups.values():
                    candidate = group["candidate"]
                    aliases = group["aliases"]
                    pieces.append(f"{candidate.name}: {_format_alias_list(aliases)}")
                    data_groups[candidate.name] = aliases
                message = "Here are the app names I remember, sir: " + "; ".join(pieces) + "."
                data = {"command": command_text, "aliases": data_groups, "implemented": True}
        event = _action_card_event(
            title="App Aliases",
            status="complete",
            target=target or "all aliases",
            message=message,
            agent_name=self.name,
        )
        return JarvisResult.ok(message, agent_name=self.name, action="list_app_aliases", data=data, events=[event])

    def _handle_focus(self, command_text: str, *, project_root: Path, dry_run: bool = False) -> JarvisResult:
        target = clean_app_target(_strip_focus_verb(command_text))
        if not target:
            return JarvisResult.fail(
                "Tell me which app you want me to bring forward, sir.",
                agent_name=self.name,
                action="focus_target",
                data={"command": command_text},
            )
        match = resolve_app_target(target, project_root, dry_run=dry_run)
        focus_result = focus_app_match(match, dry_run=dry_run)
        result_data = {
            "command": command_text,
            "target": focus_result.target,
            "requested_target": target,
            "launch_type": focus_result.launch_type,
            "focus": focus_result.to_dict(),
            "app_match": match.to_dict(),
            "implemented": True,
        }
        event = _action_card_event(
            title="Focusing Application",
            status="complete" if focus_result.success else "failed",
            target=focus_result.target,
            message=focus_result.message,
            agent_name=self.name,
        )
        if focus_result.success:
            return JarvisResult.ok(focus_result.message, agent_name=self.name, action="focus_target", data=result_data, events=[event])
        return JarvisResult.fail(focus_result.message, agent_name=self.name, action="focus_target", errors=focus_result.errors or [focus_result.message], data=result_data)

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
    """Backward-compatible single-alias parser used by older tests."""

    request = _parse_alias_management_command(command)
    if request and request.get("action") == "teach_aliases":
        aliases = list(request.get("aliases") or [])
        target = str(request.get("target") or "")
        if aliases and target:
            return aliases[0], target
    return None


def _parse_alias_management_command(command: str) -> dict[str, Any] | None:
    text = str(command or "").strip().strip(".?!")
    if not text:
        return None
    bare = re.sub(r"^(?:jarvis[, ]+)?(?:please\s+)?", "", text, flags=re.IGNORECASE).strip()

    if re.search(r"\b(?:what|list|show)\b.*\b(?:aliases|names|nicknames|app names)\b", bare, flags=re.IGNORECASE):
        target_match = re.search(r"\b(?:for|of)\s+(?P<target>.+)$", bare, flags=re.IGNORECASE)
        return {"action": "list_aliases", "target": target_match.group("target") if target_match else ""}

    rename_patterns = [
        r"^(?:change|rename)\s+(?P<old>.+?)\s+(?:to|as)\s+(?P<new>.+)$",
        r"^(?:it'?s|its)\s+(?P<new>.+?)\s+now$",
    ]
    for pattern in rename_patterns:
        match = re.match(pattern, bare, flags=re.IGNORECASE)
        if match and match.groupdict().get("old"):
            return {"action": "rename_alias", "old_alias": match.group("old"), "new_alias": match.group("new")}

    forget_patterns = [
        r"^(?:forget|remove|delete)\s+(?:the\s+)?(?:alias|name|nickname|app name|shortcut)\s+(?P<alias>.+)$",
        r"^(?:forget|remove|delete)\s+(?P<alias>.+?)\s+as\s+(?:a\s+)?(?:name|nickname|alias|app name|shortcut)(?:\s+for\s+(?P<target>.+))?$",
        r"^(?:stop\s+using|don'?t\s+use)\s+(?P<alias>.+?)\s+for\s+(?P<target>.+)$",
        r"^(?:forget\s+that\s+i\s+call|don'?t\s+call)\s+(?P<target>.+?)\s+(?P<alias>.+?)(?:\s+anymore)?$",
        r"^(?:remove)\s+(?P<alias>.+?)\s+as\s+(?:a\s+)?(?:name|nickname|alias|app name|shortcut)\s+for\s+(?P<target>.+)$",
    ]
    for pattern in forget_patterns:
        match = re.match(pattern, bare, flags=re.IGNORECASE)
        if match:
            aliases = _split_aliases(match.group("alias"))
            return {"action": "forget_aliases", "aliases": aliases, "target": match.groupdict().get("target") or ""}

    role_patterns = [
        r"^(?:use|set)\s+(?P<target>.+?)\s+as\s+(?:my\s+)?(?:main\s+|default\s+)?(?P<role>browser|music(?:\s+app)?|editor|code editor|messages|messaging(?:\s+app)?|notes|terminal|screenshots|screenshot(?:\s+tool)?|video(?:\s+player)?|media(?:\s+player)?|mail|email(?:\s+app)?)$",
        r"^(?:make)\s+(?P<target>.+?)\s+(?:my\s+)?(?:main\s+|default\s+)?(?P<role>browser|music(?:\s+app)?|editor|code editor|messages|messaging(?:\s+app)?|notes|terminal|screenshots|screenshot(?:\s+tool)?|video(?:\s+player)?|media(?:\s+player)?|mail|email(?:\s+app)?)$",
    ]
    for pattern in role_patterns:
        match = re.match(pattern, bare, flags=re.IGNORECASE)
        if match:
            return {"action": "set_role", "role": _canonical_role(match.group("role")), "target": match.group("target")}

    teach_patterns = [
        r"^(?:remember|learn)\s+(?:that\s+)?when\s+i\s+say\s+(?P<aliases>.+?)\s*,?\s*(?:open|launch|start|run)\s+(?P<target>.+)$",
        r"^when\s+i\s+say\s+(?P<aliases>.+?)\s*,?\s*(?:open|launch|start|run)\s+(?P<target>.+)$",
        r"^(?:call|name)\s+(?P<target>.+?)\s+(?P<aliases>.+)$",
        r"^(?:add)\s+(?P<aliases>.+?)\s+as\s+(?:another\s+)?(?:name|nickname|alias|app name|shortcut)\s+for\s+(?P<target>.+)$",
        r"^(?:remember|learn)\s+(?:that\s+)?(?P<aliases>.+?)\s+means\s+(?P<target>.+)$",
    ]
    for pattern in teach_patterns:
        match = re.match(pattern, bare, flags=re.IGNORECASE)
        if match:
            aliases = _split_aliases(match.group("aliases"))
            return {"action": "teach_aliases", "aliases": aliases, "target": match.group("target")}
    return None


def _split_aliases(text: str) -> list[str]:
    cleaned = str(text or "").strip().strip("'\".?!")
    cleaned = re.sub(r"\b(?:or|and)\b", ",", cleaned, flags=re.IGNORECASE)
    parts = [part.strip(" '\"	") for part in cleaned.split(",")]
    return [" ".join(part.split()) for part in parts if " ".join(part.split())]


def _clean_alias_list(aliases: list[str]) -> list[str]:
    cleaned: list[str] = []
    for alias in aliases:
        clean = normalize_query(alias)
        if clean and clean not in cleaned:
            cleaned.append(clean)
    return cleaned


def _canonical_role(role: str) -> str:
    clean = normalize_query(role)
    role_map = {
        "main browser": "browser",
        "default browser": "browser",
        "music app": "music",
        "my music app": "music",
        "code editor": "editor",
        "messaging": "messages",
        "messaging app": "messages",
        "screenshot": "screenshots",
        "screenshot tool": "screenshots",
        "video player": "video",
        "media": "video",
        "media player": "video",
        "email": "mail",
        "email app": "mail",
    }
    return role_map.get(clean, clean)


def _format_alias_list(aliases: list[str]) -> str:
    values = [str(alias) for alias in aliases if str(alias).strip()]
    if not values:
        return "nothing"
    if len(values) == 1:
        return values[0]
    if len(values) == 2:
        return f"{values[0]} and {values[1]}"
    return ", ".join(values[:-1]) + f", and {values[-1]}"


def _is_focus_command(command: str) -> bool:
    text = str(command or "").strip().lower()
    return bool(re.match(r"^(?:jarvis[, ]+)?(?:please\s+)?(?:switch\s+to|focus|bring\s+up|show)(?:\s+the)?\b", text))


def _strip_focus_verb(command: str) -> str:
    text = str(command or "").strip().strip(".?!")
    return re.sub(r"^(?:jarvis[, ]+)?(?:please\s+)?(?:switch\s+to|focus|bring\s+up|show)(?:\s+the)?\s+", "", text, flags=re.IGNORECASE).strip()


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
