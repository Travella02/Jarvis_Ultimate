"""Dependency-free mock STT provider used by tests and fallback diagnostics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.providers.stt.base import STTProviderStatus, STTRequest, STTResult


class MockSTTProvider:
    """Small local STT stand-in that never opens a microphone or model."""

    provider_name = "mock"

    def __init__(self, *, text: str = "Hello sir, this is a mock transcription.") -> None:
        self.text = text

    def status(self) -> STTProviderStatus:
        return STTProviderStatus(name=self.provider_name, available=True, ready=True, message="dependency-free placeholder STT provider")

    def transcribe(self, request: STTRequest) -> STTResult:
        audio_path = Path(request.audio_path)
        if not audio_path.exists():
            return STTResult.fail(f"Audio file does not exist: {audio_path}", provider=self.provider_name, audio_path=audio_path)
        return STTResult.ok(
            "Mock STT transcription complete.",
            provider=self.provider_name,
            text=self.text,
            audio_path=audio_path,
            language=request.language,
            data={"mock": True},
        )
