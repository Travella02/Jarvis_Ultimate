"""Mock LLM provider for stable tests and offline development."""

from __future__ import annotations

from typing import Any

from jarvis.providers.llm.base import ChatMessage, LLMResponse


class MockLLMProvider:
    provider_name = "mock"

    def __init__(self, *, model: str = "mock-model", canned_response: str | None = None) -> None:
        self.model = model
        self.canned_response = canned_response

    def complete(self, prompt: str, *, system_prompt: str | None = None) -> str:
        if self.canned_response:
            return self.canned_response
        return f"Mock LLM response to: {prompt[:80]}"

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timing: Any | None = None,
    ) -> LLMResponse:
        if timing is not None and hasattr(timing, "mark"):
            timing.mark("mock_llm.request_start", model=self.model)
        if self.canned_response:
            content = self.canned_response
        else:
            user_message = ""
            for message in reversed(messages):
                if message.get("role") == "user":
                    user_message = message.get("content", "")
                    break
            content = f"Mock Jarvis response: {user_message}" if user_message else "Mock Jarvis response."
        if timing is not None and hasattr(timing, "mark"):
            timing.mark("mock_llm.request_finished", model=self.model)
        return LLMResponse.ok(content, provider=self.provider_name, model=self.model)
