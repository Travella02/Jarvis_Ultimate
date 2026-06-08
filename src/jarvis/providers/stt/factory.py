"""Factory helpers for swappable Jarvis STT providers."""

from __future__ import annotations

from typing import Any

from jarvis.providers.stt.base import STTProvider
from jarvis.providers.stt.faster_whisper_provider import FasterWhisperSTTProvider
from jarvis.providers.stt.mock_provider import MockSTTProvider


def create_stt_provider(name: str, config: Any) -> STTProvider:
    provider = normalize_provider_name(name)
    if provider == "faster_whisper":
        return FasterWhisperSTTProvider(
            model_name=getattr(config, "stt_model", "base.en"),
            device=getattr(config, "stt_device", "cpu"),
            compute_type=getattr(config, "stt_compute_type", "int8"),
            vad_filter=bool(getattr(config, "stt_vad_filter", True)),
        )
    return MockSTTProvider(text=getattr(config, "stt_mock_text", "Hello sir, this is a mock transcription."))


def normalize_provider_name(name: str | None) -> str:
    text = str(name or "mock").strip().lower().replace("-", "_")
    if text in {"whisper", "faster_whisper", "fasterwhisper", "local_whisper"}:
        return "faster_whisper"
    return "mock"


def parse_fallback_chain(value: str | list[str] | tuple[str, ...] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        raw_items = value
    else:
        raw_items = str(value).replace(";", ",").split(",")
    seen: set[str] = set()
    chain: list[str] = []
    for item in raw_items:
        normalized = normalize_provider_name(str(item))
        if normalized not in seen:
            seen.add(normalized)
            chain.append(normalized)
    return chain
