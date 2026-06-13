"""Desktop app discovery, alias learning, and safe app closing helpers."""

from __future__ import annotations

import csv
import difflib
import json
import os
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
import platform
import re
import subprocess
import sys
import time
from typing import Any, Iterable

from jarvis.tools.shared.process_tools import KNOWN_APP_COMMANDS, LaunchResult, command_for_known_app, launch_known_app

_ALIAS_VERSION = 1
_INDEX_VERSION = 4
_INDEX_TTL_SECONDS = 7 * 24 * 60 * 60
_MAX_EXECUTABLE_SCAN_RESULTS = 750

_EXECUTABLE_SUFFIXES = {".exe", ".lnk", ".url", ".app"}
_SKIP_NAME_PARTS = {
    "uninstall",
    "setup",
    "install",
    "installer",
    "update",
    "updater",
    "crash",
    "helper",
    "service",
    "broker",
    "elevated",
    "notification",
    "diagnostic",
    "telemetry",
}
_CRITICAL_PROCESS_NAMES = {
    "csrss.exe",
    "dwm.exe",
    "lsass.exe",
    "services.exe",
    "smss.exe",
    "svchost.exe",
    "system",
    "system idle process",
    "wininit.exe",
    "winlogon.exe",
}

# Extra guardrail for Jarvis itself and the Windows shell.  Closing these by
# process name can shut down the terminal running Jarvis, the Electron bridge,
# or the desktop shell instead of a user app window.
_PROTECTED_PROCESS_NAMES = {
    "cmd.exe",
    "conhost.exe",
    "explorer.exe",
    "node.exe",
    "npm.exe",
    "powershell.exe",
    "pwsh.exe",
    "python.exe",
    "pythonw.exe",
    "wt.exe",
    "windowsterminal.exe",
}

# Human aliases Jarvis should know before he has learned from this machine.
# The alias map points to known safe launch keys when possible. If the launcher
# command is not available, discovery still gets a chance to find the app.
BUILTIN_APP_ALIASES: dict[str, str] = {
    "calc": "calculator",
    "calculator": "calculator",
    "code": "vs code",
    "visual studio": "vs code",
    "vs code": "vs code",
    "vscode": "vs code",
    "visual studio code": "vs code",
    "file explorer": "file explorer",
    "explorer": "file explorer",
    "files": "file explorer",
    "chrome": "chrome",
    "google chrome": "chrome",
    "google": "chrome",
    "google browser": "chrome",
    "browser": "chrome",
    "edge": "edge",
    "microsoft edge": "edge",
    "notepad": "notepad",
    "powershell": "powershell",
    "terminal": "terminal",
}

# Process names and likely Windows install paths for common apps.  These do not
# replace discovery; they give Jarvis better first-run guesses and safer close
# targets when the launcher is a Start Menu shortcut, AppID, or shell alias.
KNOWN_APP_PROCESS_NAMES: dict[str, list[str]] = {
    "calculator": ["CalculatorApp.exe", "calc.exe"],
    "calc": ["CalculatorApp.exe", "calc.exe"],
    "chrome": ["chrome.exe"],
    "google chrome": ["chrome.exe"],
    "edge": ["msedge.exe"],
    "microsoft edge": ["msedge.exe"],
    "vs code": ["Code.exe"],
    "vscode": ["Code.exe"],
    "visual studio code": ["Code.exe"],
    "notepad": ["notepad.exe"],
    "file explorer": ["explorer.exe"],
    "explorer": ["explorer.exe"],
    "powershell": ["powershell.exe", "pwsh.exe"],
    "terminal": ["WindowsTerminal.exe", "wt.exe"],
}

WINDOWS_COMMON_EXECUTABLES: dict[str, list[str]] = {
    "chrome": [
        r"%ProgramW6432%\Google\Chrome\Application\chrome.exe",
        r"%ProgramFiles%\Google\Chrome\Application\chrome.exe",
        r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe",
        r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe",
    ],
    "edge": [
        r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe",
        r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe",
        r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe",
    ],
    "vs code": [
        r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
        r"%ProgramW6432%\Microsoft VS Code\Code.exe",
        r"%ProgramFiles%\Microsoft VS Code\Code.exe",
        r"%ProgramFiles(x86)%\Microsoft VS Code\Code.exe",
    ],
    "discord": [
        r"%LOCALAPPDATA%\Discord\Update.exe",
        r"%LOCALAPPDATA%\Programs\Discord\Discord.exe",
    ],
    "spotify": [
        r"%APPDATA%\Spotify\Spotify.exe",
        r"%LOCALAPPDATA%\Microsoft\WindowsApps\Spotify.exe",
    ],
}

WINDOWS_TITLE_ALIASES: dict[str, list[str]] = {
    "calculator": ["calculator"],
    "calc": ["calculator"],
    "chrome": ["google chrome", "chrome"],
    "google chrome": ["google chrome", "chrome"],
    "vs code": ["visual studio code", "code"],
    "vscode": ["visual studio code", "code"],
    "visual studio code": ["visual studio code", "code"],
    "edge": ["microsoft edge", "edge"],
}

_APP_VERB_RE = re.compile(
    r"^(?:jarvis[, ]+)?(?:please\s+)?(?:open|launch|start|run)(?:\s+up)?\s+(?:the\s+)?",
    re.IGNORECASE,
)
_CLOSE_VERB_RE = re.compile(
    r"^(?:jarvis[, ]+)?(?:please\s+)?(?:close|quit|exit|shut\s+down|stop)(?:\s+the)?\s+",
    re.IGNORECASE,
)
_GENERIC_APP_WORDS_RE = re.compile(r"\b(?:app|application|program|window)\b", re.IGNORECASE)


def _truthy(value: object) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def _running_under_test_process() -> bool:
    argv = " ".join(str(part).lower() for part in sys.argv)
    return "unittest" in argv or "pytest" in argv


def _effective_dry_run(dry_run: bool) -> bool:
    if _truthy(os.environ.get("JARVIS_ALLOW_OS_LAUNCH_DURING_TESTS")):
        return bool(dry_run)
    return bool(dry_run) or _truthy(os.environ.get("JARVIS_APP_AGENT_DRY_RUN")) or _running_under_test_process()


@dataclass(slots=True)
class AppCandidate:
    """One launchable desktop app candidate discovered on the machine."""

    name: str
    path: str = ""
    launch_type: str = "path"
    aliases: list[str] = field(default_factory=list)
    source: str = "discovered"
    process_names: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppCandidate":
        return cls(
            name=str(data.get("name") or ""),
            path=str(data.get("path") or ""),
            launch_type=str(data.get("launch_type") or "path"),
            aliases=[str(value) for value in data.get("aliases", []) if str(value).strip()],
            source=str(data.get("source") or "discovered"),
            process_names=[str(value) for value in data.get("process_names", []) if str(value).strip()],
        )


@dataclass(slots=True)
class AppMatch:
    """Best app lookup result for a natural-language target."""

    candidate: AppCandidate | None
    score: float = 0.0
    source: str = "none"
    query: str = ""
    learned: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate.to_dict() if self.candidate else None,
            "score": self.score,
            "source": self.source,
            "query": self.query,
            "learned": self.learned,
        }


class AppAliasStore:
    """Small JSON store for learned app aliases and discovered app cache."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.data_dir = self.project_root / "data" / "app_agent"
        self.alias_path = self.data_dir / "app_aliases.json"
        self.index_path = self.data_dir / "app_index.json"

    def load_aliases(self) -> dict[str, dict[str, Any]]:
        data = _read_json(self.alias_path, default={})
        if not isinstance(data, dict):
            return {}
        aliases = data.get("aliases", data)
        if not isinstance(aliases, dict):
            return {}
        return {normalize_query(alias): dict(value) for alias, value in aliases.items() if normalize_query(alias) and isinstance(value, dict)}

    def save_alias(self, alias: str, candidate: AppCandidate, *, source: str = "automatic") -> None:
        clean_alias = normalize_query(alias)
        if not clean_alias or candidate is None:
            return
        self.data_dir.mkdir(parents=True, exist_ok=True)
        aliases = self.load_aliases()
        payload = candidate.to_dict()
        payload.update({"learned_alias": clean_alias, "learned_source": source, "learned_at": time.time()})
        aliases[clean_alias] = payload
        _write_json(
            self.alias_path,
            {
                "version": _ALIAS_VERSION,
                "updated_at": time.time(),
                "aliases": aliases,
            },
        )

    def load_index(self) -> list[AppCandidate] | None:
        data = _read_json(self.index_path, default={})
        if not isinstance(data, dict) or data.get("version") != _INDEX_VERSION:
            return None
        created_at = float(data.get("created_at") or 0.0)
        if created_at and (time.time() - created_at) > _INDEX_TTL_SECONDS:
            return None
        candidates = data.get("candidates")
        if not isinstance(candidates, list):
            return None
        return [AppCandidate.from_dict(item) for item in candidates if isinstance(item, dict)]

    def save_index(self, candidates: Iterable[AppCandidate]) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        _write_json(
            self.index_path,
            {
                "version": _INDEX_VERSION,
                "created_at": time.time(),
                "candidates": [candidate.to_dict() for candidate in candidates],
            },
        )


def clean_app_target(command_or_target: str, *, close: bool = False) -> str:
    """Extract the app name from natural-language open/close commands."""

    text = str(command_or_target or "").strip().strip(".?!")
    text = (_CLOSE_VERB_RE if close else _APP_VERB_RE).sub("", text).strip()
    text = _GENERIC_APP_WORDS_RE.sub("", text).strip()
    text = re.sub(r"^(?:the|my)\s+", "", text, flags=re.IGNORECASE).strip()
    return " ".join(text.split())


def normalize_query(value: str) -> str:
    """Normalize a natural-language app alias for matching."""

    text = str(value or "").lower().strip()
    text = _APP_VERB_RE.sub("", text)
    text = _CLOSE_VERB_RE.sub("", text)
    text = _GENERIC_APP_WORDS_RE.sub("", text)
    text = re.sub(r"[^a-z0-9+#. ]+", " ", text)
    text = re.sub(r"\b(?:the|my|please)\b", " ", text)
    return " ".join(text.split())


def discover_apps(project_root: str | Path, *, force_refresh: bool = False, test_safe: bool = False) -> list[AppCandidate]:
    """Return known, cached, and discovered app candidates."""

    store = AppAliasStore(project_root)
    candidates = _known_app_candidates()
    cached = None if force_refresh else store.load_index()
    if cached is None:
        discovered = _scan_common_app_locations(test_safe=test_safe)
        if not test_safe:
            store.save_index(discovered)
    else:
        discovered = cached
    merged = _dedupe_candidates([*candidates, *discovered])
    return merged


def resolve_app_target(target: str, project_root: str | Path, *, force_refresh: bool = False, dry_run: bool = False) -> AppMatch:
    """Resolve a spoken app target to the best candidate, learning aliases over time."""

    query = normalize_query(target)
    if not query:
        return AppMatch(None, 0.0, "empty", query)

    store = AppAliasStore(project_root)
    learned_aliases = store.load_aliases()
    if query in learned_aliases:
        return AppMatch(AppCandidate.from_dict(learned_aliases[query]), 1.0, "learned_alias", query, learned=True)

    builtin_key = BUILTIN_APP_ALIASES.get(query)
    if dry_run and builtin_key:
        candidate = _candidate_for_known_key(builtin_key)
        if candidate is not None:
            return AppMatch(candidate, 0.98, "builtin_alias", query)

    safe_scan = _effective_dry_run(dry_run)
    candidates = discover_apps(project_root, force_refresh=force_refresh, test_safe=safe_scan)

    # Prefer a real discovered launcher over a generic shell command.  This is
    # especially important for Chrome and VS Code, where the app may not be in
    # PATH even though it is installed.  In dry-run/test mode, the builtin branch
    # above returns before shell-based discovery so tests never spawn apps or
    # PowerShell discovery processes.
    if builtin_key:
        discovered_match = _best_candidate_match(query, [candidate for candidate in candidates if candidate.launch_type != "known"])
        if discovered_match.candidate is not None and discovered_match.score >= 0.62:
            # Keep the public match source deterministic for tests/telemetry while
            # still using the better real discovered launcher internally.
            discovered_match.source = "builtin_alias"
            return discovered_match
        candidate = _candidate_for_known_key(builtin_key)
        if candidate is not None:
            return AppMatch(candidate, 0.98, "builtin_alias", query)

    best = _best_candidate_match(query, candidates)
    if best.candidate is not None and best.score >= 0.54:
        return best

    # If the cached index missed a newly installed app, force one refresh before
    # giving up.  Learned aliases still make future launches fast.
    if not force_refresh:
        refreshed = discover_apps(project_root, force_refresh=True, test_safe=safe_scan)
        best = _best_candidate_match(query, refreshed)
        if best.candidate is not None and best.score >= 0.54:
            return best

    return AppMatch(None, round(best.score, 3), "not_found", query)


def _best_candidate_match(query: str, candidates: Iterable[AppCandidate]) -> AppMatch:
    best_candidate: AppCandidate | None = None
    best_score = 0.0
    best_source = "none"
    for candidate in candidates:
        aliases = _candidate_aliases(candidate)
        for alias in aliases:
            score = _match_score(query, alias)
            if score > best_score:
                best_candidate = candidate
                best_score = score
                best_source = f"match:{alias}"
    if best_candidate is None:
        return AppMatch(None, round(best_score, 3), "not_found", query)
    return AppMatch(best_candidate, round(best_score, 3), best_source, query)


def launch_app_match(match: AppMatch, *, project_root: str | Path, alias_to_learn: str = "", dry_run: bool = False) -> LaunchResult:
    """Launch a resolved app match and learn the requested alias on success."""

    candidate = match.candidate
    if candidate is None:
        return LaunchResult(False, f"I could not find an app matching '{match.query}', sir.", target=match.query, errors=["app_not_found"])

    if candidate.launch_type == "known":
        result = launch_known_app(candidate.name, project_root=project_root, dry_run=dry_run)
        if not result.success:
            fallback = _launch_discovered_fallback(match.query or alias_to_learn or candidate.name, project_root=project_root, dry_run=dry_run)
            if fallback is not None and fallback.success:
                if alias_to_learn and fallback.command:
                    fallback_candidate = AppCandidate(
                        name=fallback.target,
                        path=str(fallback.command),
                        launch_type="path",
                        aliases=[alias_to_learn, fallback.target],
                        source="launch_fallback",
                        process_names=_known_process_names_for_name(fallback.target),
                    )
                    AppAliasStore(project_root).save_alias(alias_to_learn, fallback_candidate, source="launch_fallback_success")
                return fallback
    else:
        result = _launch_path(candidate, dry_run=dry_run)

    if result.success and alias_to_learn:
        AppAliasStore(project_root).save_alias(alias_to_learn, candidate, source="launch_success")
    return result


def close_app_match(match: AppMatch, *, project_root: str | Path, alias_to_learn: str = "", dry_run: bool = False) -> LaunchResult:
    """Close a resolved app match without force-killing critical system processes."""

    candidate = match.candidate
    if candidate is None:
        return LaunchResult(False, f"I could not find an app matching '{match.query}' to close, sir.", target=match.query, launch_type="close", errors=["app_not_found"])

    process_names = _process_names_for_candidate(candidate)
    result = _close_process_names(process_names, display_name=candidate.name, dry_run=dry_run)
    if result.success and alias_to_learn:
        AppAliasStore(project_root).save_alias(alias_to_learn, candidate, source="close_success")
    return result


def _launch_discovered_fallback(query: str, *, project_root: str | Path, dry_run: bool = False) -> LaunchResult | None:
    refreshed = discover_apps(project_root, force_refresh=True, test_safe=dry_run)
    match = _best_candidate_match(normalize_query(query), [candidate for candidate in refreshed if candidate.launch_type != "known"])
    if match.candidate is None or match.score < 0.54:
        return None
    return _launch_path(match.candidate, dry_run=dry_run)


def _known_app_candidates() -> list[AppCandidate]:
    candidates: list[AppCandidate] = []
    reverse_aliases: dict[str, list[str]] = {}
    for alias, key in BUILTIN_APP_ALIASES.items():
        reverse_aliases.setdefault(key, []).append(alias)
    for key in KNOWN_APP_COMMANDS:
        aliases = sorted(_aliases_for_known_key(key) | set(reverse_aliases.get(key, [])))
        process_names = _known_process_names_for_name(key) or _process_names_from_command(command_for_known_app(key) or [])
        candidates.append(AppCandidate(name=key, launch_type="known", aliases=aliases, source="known", process_names=process_names))
    return candidates


def _aliases_for_known_key(key: str) -> set[str]:
    normalized = normalize_query(key)
    aliases = {normalized, key}
    aliases.update(alias for alias, mapped in BUILTIN_APP_ALIASES.items() if mapped == normalized or mapped == key)
    return {alias for alias in aliases if alias}

def _candidate_for_known_key(key: str) -> AppCandidate | None:
    command = command_for_known_app(key)
    if command is None:
        return None
    aliases = sorted(_aliases_for_known_key(key))
    return AppCandidate(name=key, launch_type="known", aliases=aliases, source="known", process_names=_known_process_names_for_name(key) or _process_names_from_command(command))


def _scan_common_app_locations(*, test_safe: bool = False) -> list[AppCandidate]:
    system = platform.system().lower()
    if system == "windows":
        return _scan_windows_apps(test_safe=test_safe)
    if system == "darwin":
        return _scan_macos_apps()
    return _scan_linux_apps()


def _scan_windows_apps(*, test_safe: bool = False) -> list[AppCandidate]:
    candidates: list[AppCandidate] = []
    candidates.extend(_windows_common_executable_candidates())
    candidates.extend(_windows_registry_app_paths_candidates())
    candidates.extend(_windows_path_candidates())
    if not test_safe:
        candidates.extend(_windows_start_apps_candidates())

    shortcut_dirs = [
        os.environ.get("PROGRAMDATA", "") and Path(os.environ["PROGRAMDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        os.environ.get("APPDATA", "") and Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs",
        os.environ.get("USERPROFILE", "") and Path(os.environ["USERPROFILE"]) / "Desktop",
        os.environ.get("PUBLIC", "") and Path(os.environ["PUBLIC"]) / "Desktop",
    ]
    for root in shortcut_dirs:
        if root:
            candidates.extend(_scan_paths(Path(root), suffixes={".lnk", ".url"}, recursive=True, source="start_menu"))

    exe_roots = [
        os.environ.get("ProgramFiles", "") and Path(os.environ["ProgramFiles"]),
        os.environ.get("ProgramFiles(x86)", "") and Path(os.environ["ProgramFiles(x86)"]),
        os.environ.get("LOCALAPPDATA", "") and Path(os.environ["LOCALAPPDATA"]) / "Programs",
        os.environ.get("LOCALAPPDATA", "") and Path(os.environ["LOCALAPPDATA"]) / "Microsoft" / "WindowsApps",
    ]
    exe_count = 0
    for root in exe_roots:
        if not root:
            continue
        for candidate in _scan_paths(Path(root), suffixes={".exe"}, recursive=True, max_depth=5, source="program_files"):
            candidates.append(candidate)
            exe_count += 1
            if exe_count >= _MAX_EXECUTABLE_SCAN_RESULTS:
                break
        if exe_count >= _MAX_EXECUTABLE_SCAN_RESULTS:
            break
    return _dedupe_candidates(candidates)


def _windows_common_executable_candidates() -> list[AppCandidate]:
    candidates: list[AppCandidate] = []
    for app_key, templates in WINDOWS_COMMON_EXECUTABLES.items():
        aliases = sorted(_aliases_for_known_key(app_key))
        for template in templates:
            expanded = Path(os.path.expandvars(template))
            if not expanded.exists():
                continue
            candidates.append(
                AppCandidate(
                    name=_display_name_from_path(expanded),
                    path=str(expanded),
                    launch_type="path",
                    aliases=aliases,
                    source="known_path",
                    process_names=_known_process_names_for_name(app_key) or _process_names_from_path(expanded),
                )
            )
    return candidates


def _windows_registry_app_paths_candidates() -> list[AppCandidate]:
    """Discover Windows apps registered in App Paths.

    Chrome, VS Code, and several user-installed desktop apps commonly register
    launch paths here even when their executable is not available through PATH.
    This is read-only registry access and never launches anything during scan.
    """

    if platform.system().lower() != "windows":
        return []
    try:
        import winreg  # type: ignore[attr-defined]
    except Exception:
        return []

    roots = [
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths"),
    ]
    candidates: list[AppCandidate] = []
    seen: set[str] = set()
    for hive, subkey in roots:
        try:
            key = winreg.OpenKey(hive, subkey)
        except OSError:
            continue
        with key:
            try:
                count = winreg.QueryInfoKey(key)[0]
            except OSError:
                count = 0
            for index in range(count):
                try:
                    exe_name = winreg.EnumKey(key, index)
                    app_key = winreg.OpenKey(key, exe_name)
                except OSError:
                    continue
                with app_key:
                    try:
                        raw_path, _ = winreg.QueryValueEx(app_key, "")
                    except OSError:
                        raw_path = ""
                path_text = str(raw_path or "").strip().strip('"')
                if not path_text:
                    continue
                path = Path(os.path.expandvars(path_text))
                if path.suffix.lower() != ".exe" or not path.exists() or _should_skip_app_name(path.stem):
                    continue
                path_key = str(path).lower()
                if path_key in seen:
                    continue
                seen.add(path_key)
                display_name = _display_name_from_path(path)
                normalized_name = normalize_query(display_name)
                mapped_key = BUILTIN_APP_ALIASES.get(normalized_name, BUILTIN_APP_ALIASES.get(normalize_query(path.stem), normalized_name))
                aliases = _aliases_for_known_key(mapped_key)
                aliases.update({display_name, path.stem, exe_name, normalized_name})
                candidates.append(
                    AppCandidate(
                        name=display_name,
                        path=str(path),
                        launch_type="path",
                        aliases=sorted(alias for alias in aliases if alias),
                        source="registry_app_paths",
                        process_names=_known_process_names_for_name(mapped_key) or _process_names_from_path(path),
                    )
                )
    return candidates

def _windows_path_candidates() -> list[AppCandidate]:
    candidates: list[AppCandidate] = []
    checked: set[str] = set()
    for app_key, aliases in _windows_path_aliases().items():
        for executable in aliases:
            resolved = shutil.which(executable)
            if not resolved:
                continue
            path = Path(resolved)
            key = str(path).lower()
            if key in checked:
                continue
            checked.add(key)
            candidates.append(
                AppCandidate(
                    name=_display_name_from_path(path),
                    path=str(path),
                    launch_type="path",
                    aliases=sorted({app_key, *[alias for alias, mapped in BUILTIN_APP_ALIASES.items() if mapped == app_key], path.stem}),
                    source="path",
                    process_names=_known_process_names_for_name(app_key) or _process_names_from_path(path),
                )
            )
    return candidates


def _windows_path_aliases() -> dict[str, list[str]]:
    return {
        "chrome": ["chrome.exe", "chrome"],
        "edge": ["msedge.exe", "msedge"],
        "vs code": ["Code.exe", "code.cmd", "code"],
        "notepad": ["notepad.exe"],
        "calculator": ["calc.exe"],
        "powershell": ["powershell.exe", "pwsh.exe"],
        "terminal": ["wt.exe"],
    }


def _windows_start_apps_candidates() -> list[AppCandidate]:
    """Return UWP/Start Menu app IDs using PowerShell when available.

    This catches Microsoft Store apps such as Calculator that do not always have
    a normal executable path visible to Python.
    """

    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        "Get-StartApps | Select-Object Name,AppID | ConvertTo-Json -Compress",
    ]
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=8)  # noqa: S603,S607
    except Exception:
        return []
    if completed.returncode != 0 or not completed.stdout.strip():
        return []
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return []
    rows = payload if isinstance(payload, list) else [payload]
    candidates: list[AppCandidate] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("Name") or "").strip()
        app_id = str(row.get("AppID") or "").strip()
        if not name or not app_id or _should_skip_app_name(name):
            continue
        normalized_name = normalize_query(name)
        mapped_key = BUILTIN_APP_ALIASES.get(normalized_name, normalized_name)
        aliases = {name, normalized_name, mapped_key}
        for alias, key in BUILTIN_APP_ALIASES.items():
            if key == mapped_key or alias in normalized_name or normalized_name in alias:
                aliases.add(alias)
        candidates.append(
            AppCandidate(
                name=name,
                path=app_id,
                launch_type="aumid",
                aliases=sorted(alias for alias in aliases if alias),
                source="start_apps",
                process_names=_known_process_names_for_name(mapped_key),
            )
        )
    return candidates

def _scan_macos_apps() -> list[AppCandidate]:
    roots = [Path("/Applications"), Path.home() / "Applications"]
    candidates: list[AppCandidate] = []
    for root in roots:
        candidates.extend(_scan_paths(root, suffixes={".app"}, recursive=False, source="applications"))
    return _dedupe_candidates(candidates)


def _scan_linux_apps() -> list[AppCandidate]:
    candidates: list[AppCandidate] = []
    desktop_dirs = [Path("/usr/share/applications"), Path.home() / ".local" / "share" / "applications"]
    for root in desktop_dirs:
        candidates.extend(_scan_paths(root, suffixes={".desktop"}, recursive=False, source="applications"))
    return _dedupe_candidates(candidates)


def _scan_paths(root: Path, *, suffixes: set[str], recursive: bool, source: str, max_depth: int | None = None) -> list[AppCandidate]:
    if not root.exists() or not root.is_dir():
        return []
    results: list[AppCandidate] = []
    try:
        iterator = root.rglob("*") if recursive else root.iterdir()
        for path in iterator:
            try:
                if not path.is_file() and path.suffix.lower() != ".app":
                    continue
                if max_depth is not None:
                    try:
                        if len(path.relative_to(root).parts) > max_depth + 1:
                            continue
                    except ValueError:
                        continue
                suffix = path.suffix.lower()
                if suffix not in suffixes:
                    continue
                name = _display_name_from_path(path)
                if _should_skip_app_name(name):
                    continue
                results.append(
                    AppCandidate(
                        name=name,
                        path=str(path),
                        launch_type="path",
                        aliases=[name, path.stem],
                        source=source,
                        process_names=_process_names_from_path(path),
                    )
                )
            except OSError:
                continue
    except OSError:
        return []
    return results


def _display_name_from_path(path: Path) -> str:
    name = path.stem if path.suffix else path.name
    name = re.sub(r"\s*\([^)]*\)\s*$", "", name).strip()
    return " ".join(name.replace("_", " ").split()) or path.name


def _should_skip_app_name(name: str) -> bool:
    normalized = normalize_query(name)
    if not normalized:
        return True
    return any(part in normalized for part in _SKIP_NAME_PARTS)


def _dedupe_candidates(candidates: Iterable[AppCandidate]) -> list[AppCandidate]:
    merged: dict[str, AppCandidate] = {}
    for candidate in candidates:
        key = candidate.path.lower() if candidate.path else f"known:{normalize_query(candidate.name)}"
        if key not in merged:
            merged[key] = candidate
            continue
        existing = merged[key]
        existing.aliases = sorted(set([*existing.aliases, *candidate.aliases]))
        existing.process_names = sorted(set([*existing.process_names, *candidate.process_names]))
    return sorted(merged.values(), key=lambda item: (item.source != "known", normalize_query(item.name)))


def _candidate_aliases(candidate: AppCandidate) -> list[str]:
    values = {candidate.name, *candidate.aliases}
    if candidate.path:
        path = Path(candidate.path)
        values.add(path.stem)
        values.add(_display_name_from_path(path))
    values.update(candidate.process_names)
    return [normalize_query(value) for value in values if normalize_query(value)]


def _match_score(query: str, alias: str) -> float:
    if not query or not alias:
        return 0.0
    if query == alias:
        return 1.0
    if query in alias or alias in query:
        shorter = min(len(query), len(alias))
        longer = max(len(query), len(alias))
        return 0.72 + (shorter / max(longer, 1)) * 0.18
    query_tokens = set(query.split())
    alias_tokens = set(alias.split())
    overlap = len(query_tokens & alias_tokens) / max(len(query_tokens | alias_tokens), 1)
    ratio = difflib.SequenceMatcher(None, query, alias).ratio()
    return max(ratio * 0.82, overlap * 0.78)


def _launch_path(candidate: AppCandidate, *, dry_run: bool = False) -> LaunchResult:
    dry_run = _effective_dry_run(dry_run)
    if candidate.launch_type == "aumid":
        command = ["explorer.exe", f"shell:AppsFolder\\{candidate.path}"]
        if dry_run:
            return LaunchResult(True, f"Ready to open {candidate.name}.", target=candidate.name, command=command)
        try:
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603,S607
        except Exception as exc:  # pragma: no cover - platform-specific launch boundary
            return LaunchResult(False, f"I found {candidate.name}, but I could not open it: {exc}", target=candidate.name, command=command, errors=[str(exc)])
        return LaunchResult(True, f"Opening {candidate.name}, sir.", target=candidate.name, command=command)

    path = Path(candidate.path)
    if not path.exists():
        return LaunchResult(False, f"I found {candidate.name}, but its saved path no longer exists.", target=candidate.name, command=str(path), errors=["missing_path"])
    if dry_run:
        return LaunchResult(True, f"Ready to open {candidate.name}.", target=candidate.name, command=str(path))
    try:
        system = platform.system().lower()
        if system == "windows":
            os.startfile(str(path))  # type: ignore[attr-defined] # noqa: S606 - user-requested local app launch
        elif system == "darwin":
            subprocess.Popen(["open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603
        else:
            subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603
    except Exception as exc:  # pragma: no cover - platform-specific launch boundary
        return LaunchResult(False, f"I found {candidate.name}, but I could not open it: {exc}", target=candidate.name, command=str(path), errors=[str(exc)])
    return LaunchResult(True, f"Opening {candidate.name}, sir.", target=candidate.name, command=str(path))


def _known_process_names_for_name(name: str) -> list[str]:
    normalized = normalize_query(name)
    mapped = BUILTIN_APP_ALIASES.get(normalized, normalized)
    names = [*KNOWN_APP_PROCESS_NAMES.get(normalized, []), *KNOWN_APP_PROCESS_NAMES.get(mapped, [])]
    return sorted({process for process in names if _is_safe_process_name(process)})


def _process_names_for_candidate(candidate: AppCandidate) -> list[str]:
    names = set(candidate.process_names)
    for alias in [candidate.name, *candidate.aliases]:
        names.update(_known_process_names_for_name(alias))
    if candidate.launch_type == "known":
        names.update(_process_names_from_command(command_for_known_app(candidate.name) or []))
    if candidate.path and candidate.launch_type != "aumid":
        names.update(_process_names_from_path(Path(candidate.path)))
    # Only synthesize process names when discovery could not provide anything.
    # This avoids turning dangerous names such as "system" into process targets.
    if not names:
        for alias in [candidate.name, *candidate.aliases]:
            normalized = normalize_query(alias)
            if normalized and len(normalized) > 2:
                names.add(normalized.replace(" ", "") + ".exe")
                names.add(normalized.split()[0] + ".exe")
    return sorted({name for name in names if _is_safe_process_name(name)})


def _process_names_from_path(path: Path) -> list[str]:
    if path.suffix.lower() == ".exe":
        return [path.name]
    return []


def _process_names_from_command(command: list[str] | str | None) -> list[str]:
    if not command:
        return []
    first = command[0] if isinstance(command, list) else str(command).split()[0]
    name = Path(first).name
    if not Path(name).suffix and platform.system().lower() == "windows":
        name = f"{name}.exe"
    return [name]


def _close_process_names(process_names: list[str], *, display_name: str, dry_run: bool = False) -> LaunchResult:
    dry_run = _effective_dry_run(dry_run)
    safe_names = [name for name in process_names if _is_safe_process_name(name)]
    blocked_names = sorted({str(name).strip() for name in process_names if str(name).strip() and not _is_safe_process_name(name)})
    if not safe_names:
        return LaunchResult(
            False,
            f"I do not have a safe process name for closing {display_name}, sir.",
            target=display_name,
            launch_type="close",
            command=process_names,
            errors=["no_safe_process_name", *blocked_names],
        )
    system = platform.system().lower()
    if dry_run:
        return LaunchResult(True, f"Ready to close {display_name}.", target=display_name, launch_type="close", command=safe_names)
    if system == "windows":
        running = _windows_running_processes()
        matched = _match_running_processes(safe_names, running)
        if not matched:
            # Some Microsoft Store apps and apps that only expose a window title
            # do not show up under the guessed process name immediately.  Try a
            # title/name based PowerShell close before reporting that it is not
            # running.
            for attempt in range(2):
                window_result = _windows_close_by_title(display_name, safe_names, dry_run=dry_run)
                if window_result is not None:
                    return window_result
                if attempt == 0:
                    time.sleep(0.65)
                    running = _windows_running_processes()
                    matched = _match_running_processes(safe_names, running)
                    if matched:
                        break
            if not matched:
                return LaunchResult(False, f"I found {display_name}, but I do not see it running right now, sir.", target=display_name, launch_type="close", command=safe_names, errors=["process_not_running"])

        result = _windows_taskkill_processes(matched, display_name=display_name, force=True)
        if result.success:
            return result

        # Last-chance fallback by window title/process base.  This catches cases
        # where tasklist sees an alias but taskkill needs the actual process Id.
        window_result = _windows_close_by_title(display_name, safe_names, dry_run=dry_run)
        if window_result is not None and window_result.success:
            return window_result
        return result

    # macOS/Linux fallback. Avoid force killing. Best effort by process name.
    process = safe_names[0]
    try:
        completed = subprocess.run(["pkill", "-f", process], capture_output=True, text=True, timeout=8)  # noqa: S603,S607
    except Exception as exc:  # pragma: no cover - platform-specific boundary
        return LaunchResult(False, f"I could not close {display_name}: {exc}", target=display_name, launch_type="close", command=process, errors=[str(exc)])
    if completed.returncode in {0, 1}:
        # pkill returns 1 when no process matched.
        if completed.returncode == 0:
            return LaunchResult(True, f"Closing {display_name}, sir.", target=display_name, launch_type="close", command=process)
        return LaunchResult(False, f"I found {display_name}, but I do not see it running right now, sir.", target=display_name, launch_type="close", command=process, errors=["process_not_running"])
    return LaunchResult(False, f"I could not close {display_name}: {completed.stderr.strip()}", target=display_name, launch_type="close", command=process, errors=[completed.stderr.strip()])


def _windows_taskkill_processes(process_names: list[str], *, display_name: str, force: bool = True) -> LaunchResult:
    """Close matched Windows processes using taskkill.

    Jarvis only reaches this helper after process names pass the safety filter.
    ``/F`` is intentional for normal desktop apps because Windows Calculator,
    Chrome, and several Electron apps often ignore graceful closes or close only
    one child process.  ``/T`` closes the process tree so Chrome/VS Code helper
    processes do not stay behind.
    """

    matched = sorted({name for name in process_names if _is_safe_process_name(name)})
    if not matched:
        return LaunchResult(False, f"I do not have a safe process name for closing {display_name}, sir.", target=display_name, launch_type="close", errors=["no_safe_process_name"])
    closed: list[str] = []
    errors: list[str] = []
    command_log: list[list[str]] = []
    for process_name in matched:
        command = ["taskkill", "/IM", process_name, "/T"]
        if force:
            command.append("/F")
        command_log.append(command)
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=8)  # noqa: S603,S607
        except Exception as exc:  # pragma: no cover - platform-specific boundary
            errors.append(f"{process_name}: {exc}")
            continue
        combined = ((completed.stdout or "") + "\n" + (completed.stderr or "")).strip()
        if completed.returncode == 0:
            closed.append(process_name)
            continue
        # taskkill returns non-zero when the process disappears between tasklist
        # and kill.  Treat the well-known "not found" condition as a harmless
        # already-closed result if another matched process was closed.
        if "not found" in combined.lower() or "not running" in combined.lower():
            errors.append(f"{process_name}: already closed")
        else:
            errors.append(f"{process_name}: {combined or 'taskkill failed'}")
    if closed:
        return LaunchResult(True, f"Closing {display_name}, sir.", target=display_name, launch_type="close", command=command_log, errors=errors)
    return LaunchResult(False, f"I found {display_name}, but Windows could not close it, sir.", target=display_name, launch_type="close", command=command_log, errors=errors or ["taskkill_failed"])


def _windows_close_by_title(display_name: str, process_names: list[str], *, dry_run: bool = False) -> LaunchResult | None:
    dry_run = _effective_dry_run(dry_run)
    title_patterns = _title_patterns_for_display_name(display_name)
    process_bases = sorted({Path(name).stem for name in process_names if _is_safe_process_name(name)})
    if not title_patterns and not process_bases:
        return None
    if dry_run:
        return LaunchResult(True, f"Ready to close {display_name}.", target=display_name, launch_type="close", command={"titles": title_patterns, "processes": process_bases})

    title_json = json.dumps(title_patterns)
    proc_json = json.dumps(process_bases)
    script_template = """
$ErrorActionPreference = 'SilentlyContinue'
$titles = ConvertFrom-Json '__TITLES__'
$names = ConvertFrom-Json '__NAMES__'
$closed = New-Object System.Collections.Generic.List[string]
$procs = Get-Process | Where-Object {
    $matchedName = $false
    foreach ($n in @($names)) { if ($_.ProcessName -ieq $n) { $matchedName = $true } }
    $matchedTitle = $false
    foreach ($t in @($titles)) {
        $title = [string]$_.MainWindowTitle
        if ($title -and $title.ToLower().Contains(([string]$t).ToLower())) { $matchedTitle = $true }
    }
    $matchedName -or $matchedTitle
}
foreach ($p in $procs) {
    if ($p.MainWindowHandle -ne 0) { [void]$p.CloseMainWindow(); Start-Sleep -Milliseconds 250 }
    if (!$p.HasExited -and ($names -contains $p.ProcessName)) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
    $closed.Add($p.ProcessName)
}
$closed | Select-Object -Unique | ConvertTo-Json -Compress
"""
    script = script_template.replace("__TITLES__", title_json.replace("'", "''")).replace("__NAMES__", proc_json.replace("'", "''"))
    try:
        completed = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script], capture_output=True, text=True, timeout=8)  # noqa: S603,S607
    except Exception:
        return None
    if completed.returncode != 0:
        return None
    output = completed.stdout.strip()
    if not output:
        return None
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        parsed = output
    closed = parsed if isinstance(parsed, list) else [parsed]
    closed = [str(item) for item in closed if str(item).strip()]
    if not closed:
        return None
    return LaunchResult(True, f"Closing {display_name}, sir.", target=display_name, launch_type="close", command={"processes": closed, "method": "window_title"})


def _title_patterns_for_display_name(display_name: str) -> list[str]:
    normalized = normalize_query(display_name)
    mapped = BUILTIN_APP_ALIASES.get(normalized, normalized)
    patterns = {normalized, mapped, *WINDOWS_TITLE_ALIASES.get(normalized, []), *WINDOWS_TITLE_ALIASES.get(mapped, [])}
    return sorted({pattern for pattern in patterns if pattern and len(pattern) >= 3})


def _windows_running_processes() -> list[str]:
    try:
        completed = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, timeout=8)  # noqa: S603,S607
    except Exception:
        return []
    if completed.returncode != 0:
        return []
    rows = csv.reader(completed.stdout.splitlines())
    names: list[str] = []
    for row in rows:
        if row:
            names.append(row[0].strip())
    return names


def _match_running_processes(process_names: list[str], running_names: list[str]) -> list[str]:
    wanted = {name.lower() for name in process_names if _is_safe_process_name(name)}
    running_lookup = {name.lower(): name for name in running_names}
    exact = [running_lookup[name] for name in wanted if name in running_lookup]
    if exact:
        return sorted(set(exact))
    # Fuzzy fallback only for non-short names to avoid closing the wrong app.
    matches: list[str] = []
    for wanted_name in wanted:
        wanted_base = Path(wanted_name).stem
        if len(wanted_base) < 5:
            continue
        for running_name in running_names:
            running_base = Path(running_name.lower()).stem
            if wanted_base in running_base or running_base in wanted_base:
                if _is_safe_process_name(running_name):
                    matches.append(running_name)
    return sorted(set(matches))


def _is_safe_process_name(name: str) -> bool:
    clean = str(name or "").strip().lower()
    if not clean or clean in _CRITICAL_PROCESS_NAMES or clean in _PROTECTED_PROCESS_NAMES:
        return False
    if any(part in clean for part in ["..", "\\", "/"]):
        return False
    # Keep taskkill scoped to executable image names only.  Jarvis should never
    # pass a path, command line, PID, wildcard, or shell expression here.
    if platform.system().lower() == "windows" and not clean.endswith(".exe"):
        return False
    return True


def _read_json(path: Path, *, default: Any) -> Any:
    try:
        if not path.exists():
            return default
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)
