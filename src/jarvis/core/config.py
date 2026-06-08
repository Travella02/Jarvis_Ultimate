"""Config helpers for Jarvis 3.

The project intentionally keeps config dependency-free right now. Environment
variables always win. Jarvis also reads a simple project-root ``.env`` file so
local LM Studio settings can be changed without touching committed YAML.
The simple providers.yaml reader supports the small subset of YAML used by
Jarvis's starter config.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


_ENV_ALIASES = {
    "environment": ("JARVIS_ENV",),
    "llm_provider": ("JARVIS_LLM_PROVIDER", "JARVIS_LM_PROVIDER"),
    "llm_model": ("JARVIS_LLM_MODEL", "JARVIS_LM_MODEL"),
    "llm_base_url": ("JARVIS_LM_STUDIO_BASE_URL", "JARVIS_LLM_STUDIO_BASE_URL", "JARVIS_LLM_BASE_URL"),
    "llm_timeout_seconds": ("JARVIS_LLM_TIMEOUT_SECONDS", "JARVIS_LM_TIMEOUT_SECONDS"),
    "llm_temperature": ("JARVIS_LLM_TEMPERATURE", "JARVIS_LM_TEMPERATURE"),
    "llm_max_tokens": ("JARVIS_LLM_MAX_TOKENS", "JARVIS_LM_MAX_TOKENS"),
    "llm_resolve_auto_model": ("JARVIS_LLM_RESOLVE_AUTO_MODEL", "JARVIS_LM_RESOLVE_AUTO_MODEL"),
    "llm_streaming": ("JARVIS_LLM_STREAMING", "JARVIS_LM_STREAMING"),
}


def _read_simple_provider_config(path: Path) -> dict[str, Any]:
    """Read the small providers.yaml shape Jarvis uses without PyYAML.

    Supported shape:

        providers:
          llm:
            default: lm_studio
            model: auto
            base_url: http://localhost:1234/v1
            streaming: true
    """
    if not path.exists():
        return {}

    data: dict[str, Any] = {}
    in_llm = False
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        stripped = line.strip()
        indent = len(line) - len(line.lstrip(" "))
        if indent == 2 and stripped == "llm:":
            in_llm = True
            continue
        if indent <= 2 and stripped.endswith(":") and stripped != "llm:":
            in_llm = False
        if in_llm and indent >= 4 and ":" in stripped:
            key, value = stripped.split(":", 1)
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def _read_simple_env_file(path: Path) -> dict[str, str]:
    """Read a small KEY=value .env file without adding a dependency.

    This intentionally supports only the normal Jarvis settings style. It skips
    comments and blank lines, strips optional single/double quotes, and does not
    modify ``os.environ``.
    """
    if not path.exists():
        return {}

    data: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        data[key] = value
    return data


def _setting(names: Iterable[str], env_file: dict[str, str], default: Any) -> Any:
    """Resolve a config value with OS environment taking highest priority."""
    for name in names:
        value = os.getenv(name)
        if value is not None:
            return value
    for name in names:
        if name in env_file:
            return env_file[name]
    return default


def _as_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


@dataclass(slots=True)
class JarvisConfig:
    project_root: Path = field(default_factory=lambda: Path.cwd())
    logs_dir: Path = field(default_factory=lambda: Path("logs"))
    data_dir: Path = field(default_factory=lambda: Path("data"))
    environment: str = "development"
    debug: bool = True

    llm_provider: str = "lm_studio"
    llm_model: str = "auto"
    llm_base_url: str = "http://localhost:1234/v1"
    llm_timeout_seconds: float = 90.0
    llm_temperature: float = 0.7
    llm_max_tokens: int = 512
    llm_resolve_auto_model: bool = False
    llm_streaming: bool = True

    @classmethod
    def from_project_root(cls, project_root: str | Path | None = None) -> "JarvisConfig":
        root = Path(project_root) if project_root else Path.cwd()
        provider_config = _read_simple_provider_config(root / "config" / "providers.yaml")
        env_file = _read_simple_env_file(root / ".env")

        return cls(
            project_root=root,
            logs_dir=root / "logs",
            data_dir=root / "data",
            environment=str(_setting(_ENV_ALIASES["environment"], env_file, "development")),
            llm_provider=str(_setting(_ENV_ALIASES["llm_provider"], env_file, provider_config.get("default", "lm_studio"))),
            llm_model=str(_setting(_ENV_ALIASES["llm_model"], env_file, provider_config.get("model", "auto"))),
            llm_base_url=str(_setting(_ENV_ALIASES["llm_base_url"], env_file, provider_config.get("base_url", "http://localhost:1234/v1"))),
            llm_timeout_seconds=float(_setting(_ENV_ALIASES["llm_timeout_seconds"], env_file, provider_config.get("timeout_seconds", "90"))),
            llm_temperature=float(_setting(_ENV_ALIASES["llm_temperature"], env_file, provider_config.get("temperature", "0.7"))),
            llm_max_tokens=int(_setting(_ENV_ALIASES["llm_max_tokens"], env_file, provider_config.get("max_tokens", "512"))),
            llm_resolve_auto_model=_as_bool(
                _setting(_ENV_ALIASES["llm_resolve_auto_model"], env_file, provider_config.get("resolve_auto_model", "false")),
                default=False,
            ),
            llm_streaming=_as_bool(
                _setting(_ENV_ALIASES["llm_streaming"], env_file, provider_config.get("streaming", "true")),
                default=True,
            ),
        )
