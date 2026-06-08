"""Text-to-speech provider interfaces for Jarvis.

0.0.7 keeps TTS provider loading optional and lazy. Heavy engines such as
XTTS/Kokoro are not imported unless the provider is selected and asked to
synthesize audio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


@dataclass(slots=True)
class TTSRequest:
    """Standard input sent to TTS providers."""

    text: str
    output_path: Path
    voice_name: str = "jarvis"
    language: str = "en"
    speaker_wav: Path | None = None
    play_audio: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TTSResult:
    """Standard result returned by TTS providers and the TTS manager."""

    success: bool
    provider: str
    message: str
    output_path: Path | None = None
    played: bool = False
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(
        cls,
        message: str,
        *,
        provider: str,
        output_path: Path | None = None,
        played: bool = False,
        data: dict[str, Any] | None = None,
    ) -> "TTSResult":
        return cls(success=True, provider=provider, message=message, output_path=output_path, played=played, data=data or {})

    @classmethod
    def fail(
        cls,
        message: str,
        *,
        provider: str,
        error: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> "TTSResult":
        return cls(success=False, provider=provider, message=message, error=error or message, data=data or {})


@dataclass(slots=True)
class TTSProviderStatus:
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


class TTSProvider(Protocol):
    """Protocol implemented by all Jarvis TTS providers."""

    provider_name: str

    def status(self) -> TTSProviderStatus:
        ...

    def synthesize(self, request: TTSRequest) -> TTSResult:
        ...
