"""Speech-to-text provider interfaces for Jarvis.

0.0.9 keeps microphone/STT dependencies optional and lazy. Heavy engines such
as faster-whisper are not imported unless the provider is selected and asked to
transcribe audio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(slots=True)
class STTRequest:
    """Standard input sent to STT providers."""

    audio_path: Path
    language: str | None = None
    prompt: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class STTResult:
    """Standard result returned by STT providers and the STT manager."""

    success: bool
    provider: str
    message: str
    text: str = ""
    audio_path: Path | None = None
    language: str | None = None
    duration_seconds: float | None = None
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(
        cls,
        message: str,
        *,
        provider: str,
        text: str,
        audio_path: Path | None = None,
        language: str | None = None,
        duration_seconds: float | None = None,
        data: dict[str, Any] | None = None,
    ) -> "STTResult":
        return cls(
            success=True,
            provider=provider,
            message=message,
            text=text,
            audio_path=audio_path,
            language=language,
            duration_seconds=duration_seconds,
            data=data or {},
        )

    @classmethod
    def fail(
        cls,
        message: str,
        *,
        provider: str,
        audio_path: Path | None = None,
        error: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> "STTResult":
        return cls(success=False, provider=provider, message=message, audio_path=audio_path, error=error or message, data=data or {})


@dataclass(slots=True)
class STTProviderStatus:
    """Small provider status object used for CLI diagnostics."""

    name: str
    available: bool
    ready: bool = False
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def format_line(self) -> str:
        state = "ready" if self.ready else "available" if self.available else "unavailable"
        suffix = f" - {self.message}" if self.message else ""
        return f"{self.name}: {state}{suffix}"


class STTProvider(Protocol):
    """Protocol implemented by all Jarvis STT providers."""

    provider_name: str

    def status(self) -> STTProviderStatus:
        ...

    def transcribe(self, request: STTRequest) -> STTResult:
        ...


def format_stt_result(result: STTResult) -> str:
    """Format a STT result for the CLI."""
    lines = [result.message]
    if result.text:
        lines.append(f"Heard: {result.text}")
    lines.append(f"Provider: {result.provider}")
    if result.audio_path:
        lines.append(f"Audio: {result.audio_path}")
    if result.language:
        lines.append(f"Language: {result.language}")
    if result.duration_seconds is not None:
        lines.append(f"Audio duration: {result.duration_seconds:.2f}s")
    if result.error:
        lines.append(f"Error: {result.error}")
    return "\n".join(lines)
