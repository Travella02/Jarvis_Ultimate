"""Config helpers for Jarvis 3.

The project intentionally keeps config dependency-free right now. Environment
variables always win. The simple providers.yaml reader supports the small
subset of YAML used by Jarvis's starter config.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _read_simple_provider_config(path: Path) -> dict[str, Any]:
    """Read the small providers.yaml shape Jarvis uses without PyYAML.

    Supported shape:

        providers:
          llm:
            default: lm_studio
            model: auto
            base_url: http://localhost:1234/v1
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

    @classmethod
    def from_project_root(cls, project_root: str | Path | None = None) -> "JarvisConfig":
        root = Path(project_root) if project_root else Path.cwd()
        provider_config = _read_simple_provider_config(root / "config" / "providers.yaml")

        return cls(
            project_root=root,
            logs_dir=root / "logs",
            data_dir=root / "data",
            environment=os.getenv("JARVIS_ENV", "development"),
            llm_provider=os.getenv("JARVIS_LLM_PROVIDER", str(provider_config.get("default", "lm_studio"))),
            llm_model=os.getenv("JARVIS_LLM_MODEL", str(provider_config.get("model", "auto"))),
            llm_base_url=os.getenv("JARVIS_LM_STUDIO_BASE_URL", str(provider_config.get("base_url", "http://localhost:1234/v1"))),
            llm_timeout_seconds=float(os.getenv("JARVIS_LLM_TIMEOUT_SECONDS", str(provider_config.get("timeout_seconds", "90")))),
            llm_temperature=float(os.getenv("JARVIS_LLM_TEMPERATURE", str(provider_config.get("temperature", "0.7")))),
            llm_max_tokens=int(os.getenv("JARVIS_LLM_MAX_TOKENS", str(provider_config.get("max_tokens", "512")))),
            llm_resolve_auto_model=_as_bool(
                os.getenv("JARVIS_LLM_RESOLVE_AUTO_MODEL", provider_config.get("resolve_auto_model", "false")),
                default=False,
            ),
        )
