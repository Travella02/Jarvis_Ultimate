"""Safe process/app helpers for early Jarvis abilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import platform
import re
import subprocess
import webbrowser
from typing import Any


@dataclass(slots=True)
class LaunchResult:
    success: bool
    message: str
    target: str
    launch_type: str = "app"
    command: list[str] | str | None = None
    errors: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "message": self.message,
            "target": self.target,
            "launch_type": self.launch_type,
            "command": self.command,
            "errors": list(self.errors or []),
        }


KNOWN_APP_COMMANDS: dict[str, dict[str, list[str] | str]] = {
    "notepad": {"windows": ["notepad.exe"], "default": ["notepad"]},
    "calculator": {"windows": ["calc.exe"], "default": ["gnome-calculator"]},
    "calc": {"windows": ["calc.exe"], "default": ["gnome-calculator"]},
    "file explorer": {"windows": ["explorer.exe"], "darwin": ["open", "."], "default": ["xdg-open", "."]},
    "explorer": {"windows": ["explorer.exe"], "darwin": ["open", "."], "default": ["xdg-open", "."]},
    "vs code": {"windows": ["code"], "darwin": ["open", "-a", "Visual Studio Code"], "default": ["code"]},
    "vscode": {"windows": ["code"], "darwin": ["open", "-a", "Visual Studio Code"], "default": ["code"]},
    "visual studio code": {"windows": ["code"], "darwin": ["open", "-a", "Visual Studio Code"], "default": ["code"]},
    "chrome": {"windows": ["chrome"], "darwin": ["open", "-a", "Google Chrome"], "default": ["google-chrome"]},
    "google chrome": {"windows": ["chrome"], "darwin": ["open", "-a", "Google Chrome"], "default": ["google-chrome"]},
    "edge": {"windows": ["msedge"], "darwin": ["open", "-a", "Microsoft Edge"], "default": ["microsoft-edge"]},
    "microsoft edge": {"windows": ["msedge"], "darwin": ["open", "-a", "Microsoft Edge"], "default": ["microsoft-edge"]},
    "powershell": {"windows": ["powershell.exe"], "default": ["pwsh"]},
    "terminal": {"windows": ["wt.exe"], "darwin": ["open", "-a", "Terminal"], "default": ["x-terminal-emulator"]},
}

KNOWN_WEBSITES: dict[str, str] = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "github": "https://github.com",
    "chatgpt": "https://chatgpt.com",
    "openai": "https://openai.com",
    "spotify": "https://open.spotify.com",
}

_COMMAND_PREFIX_RE = re.compile(r"^(?:jarvis[, ]+)?(?:please\s+)?(?:open|launch|start)(?:\s+up)?\s+(?:the\s+)?", re.IGNORECASE)


def clean_launch_target(command: str) -> str:
    text = str(command or "").strip().strip(".?!")
    text = _COMMAND_PREFIX_RE.sub("", text).strip()
    text = re.sub(r"^(?:app|application|program|website|site)\s+", "", text, flags=re.IGNORECASE).strip()
    return " ".join(text.split())


def normalize_app_name(value: str) -> str:
    text = clean_launch_target(value).lower()
    aliases = {
        "code": "vs code",
        "visual studio": "vs code",
        "visual studio code": "visual studio code",
        "files": "file explorer",
        "file folder": "file explorer",
        "project folder": "file explorer",
        "jarvis folder": "file explorer",
        "jarvis project folder": "file explorer",
    }
    return aliases.get(text, text)


def looks_like_url_or_domain(target: str) -> bool:
    text = str(target or "").strip().lower()
    if text.startswith(("http://", "https://")):
        return True
    return bool(re.match(r"^[a-z0-9][a-z0-9.-]+\.[a-z]{2,}(?:/.*)?$", text))


def normalize_url(target: str) -> str:
    text = clean_launch_target(target).strip()
    lower = text.lower()
    if lower in KNOWN_WEBSITES:
        return KNOWN_WEBSITES[lower]
    if looks_like_url_or_domain(text) and not lower.startswith(("http://", "https://")):
        return f"https://{text}"
    return text


def command_for_known_app(app_name: str, *, project_root: str | Path | None = None) -> list[str] | None:
    normalized = normalize_app_name(app_name)
    system = platform.system().lower()
    key = "windows" if system == "windows" else "darwin" if system == "darwin" else "default"
    command_map = KNOWN_APP_COMMANDS.get(normalized)
    if command_map is None:
        return None
    command = list(command_map.get(key) or command_map.get("default") or [])
    if normalized == "file explorer" and project_root:
        if system == "windows":
            command = ["explorer.exe", str(Path(project_root))]
        elif system == "darwin":
            command = ["open", str(Path(project_root))]
        else:
            command = ["xdg-open", str(Path(project_root))]
    return command


def launch_known_app(app_name: str, *, project_root: str | Path | None = None, dry_run: bool = False) -> LaunchResult:
    normalized = normalize_app_name(app_name)
    command = command_for_known_app(normalized, project_root=project_root)
    if command is None:
        known = ", ".join(sorted(set(KNOWN_APP_COMMANDS)))
        return LaunchResult(False, f"I do not have a safe launcher configured for '{clean_launch_target(app_name)}' yet. Known apps: {known}.", target=normalized, errors=["unknown_app"])
    if dry_run:
        return LaunchResult(True, f"Ready to open {normalized}.", target=normalized, command=command)
    try:
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # noqa: S603 - allowlisted commands only
    except FileNotFoundError as exc:
        return LaunchResult(False, f"I could not find the launcher for {normalized}. It may not be installed or in PATH.", target=normalized, command=command, errors=[str(exc)])
    except Exception as exc:  # pragma: no cover - platform-specific launcher boundary
        return LaunchResult(False, f"I could not open {normalized}: {exc}", target=normalized, command=command, errors=[str(exc)])
    return LaunchResult(True, f"Opening {normalized}, sir.", target=normalized, command=command)


def open_website(target: str, *, dry_run: bool = False) -> LaunchResult:
    url = normalize_url(target)
    if not (looks_like_url_or_domain(url) or url.lower().startswith(("http://", "https://")) or url in KNOWN_WEBSITES.values()):
        return LaunchResult(False, f"I could not recognize '{target}' as a safe website yet.", target=target, launch_type="website", errors=["unknown_website"])
    if dry_run:
        return LaunchResult(True, f"Ready to open {url}.", target=url, launch_type="website", command=url)
    try:
        opened = webbrowser.open(url)
    except Exception as exc:  # pragma: no cover - platform-specific browser boundary
        return LaunchResult(False, f"I could not open {url}: {exc}", target=url, launch_type="website", command=url, errors=[str(exc)])
    if not opened:
        return LaunchResult(False, f"Your system did not accept the request to open {url}.", target=url, launch_type="website", command=url, errors=["browser_rejected"])
    return LaunchResult(True, f"Opening {url}, sir.", target=url, launch_type="website", command=url)
