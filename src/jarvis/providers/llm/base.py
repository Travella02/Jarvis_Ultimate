"""LLM provider interfaces and result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


ChatMessage = dict[str, str]
LLMStreamCallback = Callable[[str], None]


@dataclass(slots=True)
class LLMResponse:
    """Standard response returned by all LLM providers."""

    success: bool
    content: str
    provider: str = "unknown"
    model: str = "unknown"
    error: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, content: str, *, provider: str, model: str = "unknown", raw: dict[str, Any] | None = None) -> "LLMResponse":
        return cls(success=True, content=content, provider=provider, model=model, raw=raw or {})

    @classmethod
    def fail(cls, error: str, *, provider: str, model: str = "unknown", raw: dict[str, Any] | None = None) -> "LLMResponse":
        return cls(success=False, content="", provider=provider, model=model, error=error, raw=raw or {})


class LLMProvider(Protocol):
    provider_name: str

    def complete(self, prompt: str, *, system_prompt: str | None = None) -> str:
        ...

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timing: Any | None = None,
        stream_callback: LLMStreamCallback | None = None,
        stream: bool | None = None,
    ) -> LLMResponse:
        ...
