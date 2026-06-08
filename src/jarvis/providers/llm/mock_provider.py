"""Mock LLM provider for stable tests."""

from __future__ import annotations


class MockLLMProvider:
    def complete(self, prompt: str) -> str:
        return "Mock LLM response. Real local model provider comes later."
