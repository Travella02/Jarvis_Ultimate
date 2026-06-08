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
    "llm_api_mode": ("JARVIS_LLM_API_MODE", "JARVIS_LM_API_MODE"),
    "llm_native_base_url": ("JARVIS_LM_STUDIO_NATIVE_BASE_URL", "JARVIS_LLM_STUDIO_NATIVE_BASE_URL", "JARVIS_LLM_NATIVE_BASE_URL", "JARVIS_LM_NATIVE_BASE_URL"),
    "llm_reasoning": ("JARVIS_LLM_REASONING", "JARVIS_LM_REASONING", "JARVIS_LM_THINKING"),
    "llm_context_length": ("JARVIS_LLM_CONTEXT_LENGTH", "JARVIS_LM_CONTEXT_LENGTH"),
    "llm_store_native_chats": ("JARVIS_LLM_STORE_NATIVE_CHATS", "JARVIS_LM_STORE_NATIVE_CHATS"),
    "conversation_prompt_mode": ("JARVIS_CONVERSATION_PROMPT_MODE", "JARVIS_CHAT_SYSTEM_PROMPT_MODE", "JARVIS_LLM_PROMPT_MODE"),
    "llm_benchmark_max_tokens": ("JARVIS_LLM_BENCHMARK_MAX_TOKENS", "JARVIS_LM_BENCHMARK_MAX_TOKENS"),
    "llm_benchmark_prompt": ("JARVIS_LLM_BENCHMARK_PROMPT", "JARVIS_LM_BENCHMARK_PROMPT"),
    "memory_short_term_enabled": ("JARVIS_MEMORY_SHORT_TERM_ENABLED", "JARVIS_STM_ENABLED"),
    "memory_short_term_max_turns": ("JARVIS_MEMORY_SHORT_TERM_MAX_TURNS", "JARVIS_STM_MAX_TURNS"),
    "memory_short_term_max_chars": ("JARVIS_MEMORY_SHORT_TERM_MAX_CHARS", "JARVIS_STM_MAX_CHARS"),
    "memory_short_term_inject_last_turns": ("JARVIS_MEMORY_SHORT_TERM_INJECT_LAST_TURNS", "JARVIS_STM_INJECT_LAST_TURNS"),
    "memory_short_term_autosave": ("JARVIS_MEMORY_SHORT_TERM_AUTOSAVE", "JARVIS_STM_AUTOSAVE"),
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


def _normalize_prompt_mode(value: Any) -> str:
    text = str(value or "normal").strip().lower().replace("-", "_")
    if text in {"minimal", "small", "short", "fast"}:
        return "minimal"
    if text in {"off", "none", "no_system", "disabled", "false", "0"}:
        return "off"
    return "normal"


def _as_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"auto", "default", "none", "off", "0"}:
        return None
    try:
        number = int(text)
    except ValueError:
        return None
    return number if number > 0 else None


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
    llm_base_url: str = "http://127.0.0.1:1234/v1"
    llm_timeout_seconds: float = 90.0
    llm_temperature: float = 0.7
    llm_max_tokens: int = 512
    llm_resolve_auto_model: bool = False
    llm_streaming: bool = True
    llm_api_mode: str = "openai"
    llm_native_base_url: str = "http://127.0.0.1:1234"
    llm_reasoning: str = "auto"
    llm_context_length: int | None = None
    llm_store_native_chats: bool = False
    conversation_prompt_mode: str = "normal"
    llm_benchmark_max_tokens: int = 64
    llm_benchmark_prompt: str = "Reply with exactly one short sentence saying you are ready."

    memory_short_term_enabled: bool = True
    memory_short_term_max_turns: int = 20
    memory_short_term_max_chars: int = 12_000
    memory_short_term_inject_last_turns: int = 8
    memory_short_term_autosave: bool = False

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
            llm_base_url=str(_setting(_ENV_ALIASES["llm_base_url"], env_file, provider_config.get("base_url", "http://127.0.0.1:1234/v1"))),
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
            llm_api_mode=str(_setting(_ENV_ALIASES["llm_api_mode"], env_file, provider_config.get("api_mode", "openai"))).strip().lower(),
            llm_native_base_url=str(
                _setting(_ENV_ALIASES["llm_native_base_url"], env_file, provider_config.get("native_base_url", "http://127.0.0.1:1234"))
            ),
            llm_reasoning=str(_setting(_ENV_ALIASES["llm_reasoning"], env_file, provider_config.get("reasoning", "auto"))).strip().lower(),
            llm_context_length=_as_optional_int(_setting(_ENV_ALIASES["llm_context_length"], env_file, provider_config.get("context_length", ""))),
            llm_store_native_chats=_as_bool(
                _setting(_ENV_ALIASES["llm_store_native_chats"], env_file, provider_config.get("store_native_chats", "false")),
                default=False,
            ),
            conversation_prompt_mode=_normalize_prompt_mode(
                _setting(_ENV_ALIASES["conversation_prompt_mode"], env_file, provider_config.get("conversation_prompt_mode", "normal"))
            ),
            llm_benchmark_max_tokens=int(
                _setting(_ENV_ALIASES["llm_benchmark_max_tokens"], env_file, provider_config.get("benchmark_max_tokens", "64"))
            ),
            llm_benchmark_prompt=str(
                _setting(
                    _ENV_ALIASES["llm_benchmark_prompt"],
                    env_file,
                    provider_config.get("benchmark_prompt", "Reply with exactly one short sentence saying you are ready."),
                )
            ),
            memory_short_term_enabled=_as_bool(
                _setting(_ENV_ALIASES["memory_short_term_enabled"], env_file, provider_config.get("memory_short_term_enabled", "true")),
                default=True,
            ),
            memory_short_term_max_turns=int(
                _setting(_ENV_ALIASES["memory_short_term_max_turns"], env_file, provider_config.get("memory_short_term_max_turns", "20"))
            ),
            memory_short_term_max_chars=int(
                _setting(_ENV_ALIASES["memory_short_term_max_chars"], env_file, provider_config.get("memory_short_term_max_chars", "12000"))
            ),
            memory_short_term_inject_last_turns=int(
                _setting(
                    _ENV_ALIASES["memory_short_term_inject_last_turns"],
                    env_file,
                    provider_config.get("memory_short_term_inject_last_turns", "8"),
                )
            ),
            memory_short_term_autosave=_as_bool(
                _setting(_ENV_ALIASES["memory_short_term_autosave"], env_file, provider_config.get("memory_short_term_autosave", "false")),
                default=False,
            ),
        )
