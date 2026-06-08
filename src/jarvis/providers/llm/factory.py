"""Factory for creating the configured Jarvis LLM provider."""

from __future__ import annotations

from typing import Any

from jarvis.providers.llm.lm_studio_provider import LMStudioProvider
from jarvis.providers.llm.mock_provider import MockLLMProvider


def create_llm_provider(config: Any | None = None):
    provider_name = getattr(config, "llm_provider", "lm_studio") if config else "lm_studio"
    provider_name = str(provider_name).strip().lower()

    if provider_name in {"mock", "test"}:
        return MockLLMProvider(model=getattr(config, "llm_model", "mock-model"))

    if provider_name in {"lm_studio", "lmstudio", "local"}:
        return LMStudioProvider(
            base_url=getattr(config, "llm_base_url", "http://localhost:1234/v1"),
            model=getattr(config, "llm_model", "auto"),
            timeout_seconds=float(getattr(config, "llm_timeout_seconds", 90.0)),
            temperature=float(getattr(config, "llm_temperature", 0.7)),
            max_tokens=int(getattr(config, "llm_max_tokens", 512)),
            resolve_auto_model=bool(getattr(config, "llm_resolve_auto_model", False)),
        )

    # Safe fallback for unknown provider names.
    return MockLLMProvider(model="unknown-provider-fallback", canned_response=f"Unknown LLM provider '{provider_name}'. Falling back to mock mode.")
