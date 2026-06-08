"""Factory helpers for swappable Jarvis TTS providers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.providers.tts.base import TTSProvider
from jarvis.providers.tts.kokoro_provider import KokoroTTSProvider
from jarvis.providers.tts.mock_provider import MockTTSProvider
from jarvis.providers.tts.xtts_provider import XTTSTTSProvider


def create_tts_provider(name: str, config: Any) -> TTSProvider:
    """Create a TTS provider by name without loading heavy models yet."""
    provider = normalize_provider_name(name)
    if provider == "xtts":
        speaker_wav = getattr(config, "tts_xtts_speaker_wav", "")
        return XTTSTTSProvider(
            model_name=getattr(config, "tts_xtts_model_name", "tts_models/multilingual/multi-dataset/xtts_v2"),
            use_gpu=bool(getattr(config, "tts_use_gpu", True)),
            device=getattr(config, "tts_device", "cuda"),
            speaker_wav=speaker_wav or None,
        )
    if provider == "kokoro":
        return KokoroTTSProvider(
            voice_name=getattr(config, "tts_kokoro_voice", "af_heart"),
            lang_code=getattr(config, "tts_kokoro_lang_code", "a"),
        )
    return MockTTSProvider()


def normalize_provider_name(name: str | None) -> str:
    text = str(name or "mock").strip().lower().replace("-", "_")
    if text in {"xtts", "xtts_v2", "coqui", "coqui_xtts"}:
        return "xtts"
    if text in {"kokoro", "kokoro_tts"}:
        return "kokoro"
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
