"""LM Studio OpenAI-compatible LLM provider.

This provider talks to LM Studio's local OpenAI-compatible API, normally at:

    http://localhost:1234/v1

It intentionally uses only Python standard library modules so Jarvis 0.0.3
does not require an extra dependency just to talk to a local model.
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any, Callable

from jarvis.providers.llm.base import ChatMessage, LLMResponse


UrlOpen = Callable[..., Any]


class LMStudioProvider:
    provider_name = "lm_studio"

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:1234/v1",
        model: str = "auto",
        timeout_seconds: float = 90.0,
        temperature: float = 0.7,
        max_tokens: int = 512,
        urlopen: UrlOpen | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model or "auto"
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._urlopen = urlopen or urllib.request.urlopen
        self._resolved_model: str | None = None

    def complete(self, prompt: str, *, system_prompt: str | None = None) -> str:
        response = self.chat([{"role": "user", "content": prompt}], system_prompt=system_prompt)
        if response.success:
            return response.content
        return f"LM Studio provider error: {response.error}"

    def chat(
        self,
        messages: list[ChatMessage],
        *,
        system_prompt: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        prepared_messages = self._prepare_messages(messages, system_prompt=system_prompt)
        model = self.resolve_model()
        payload = {
            "model": model,
            "messages": prepared_messages,
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": self.max_tokens if max_tokens is None else max_tokens,
        }

        try:
            raw = self._request_json("POST", "/chat/completions", payload=payload)
            content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                return LLMResponse.fail("LM Studio returned an empty response.", provider=self.provider_name, model=model, raw=raw)
            return LLMResponse.ok(content.strip(), provider=self.provider_name, model=model, raw=raw)
        except Exception as exc:
            return LLMResponse.fail(self._friendly_error(exc), provider=self.provider_name, model=model)

    def list_models(self) -> list[str]:
        try:
            raw = self._request_json("GET", "/models")
        except Exception:
            return []
        models = raw.get("data", [])
        names: list[str] = []
        for item in models:
            model_id = item.get("id") if isinstance(item, dict) else None
            if model_id:
                names.append(str(model_id))
        return names

    def health_check(self) -> bool:
        return bool(self.list_models())

    def resolve_model(self) -> str:
        if self.model.lower() not in {"", "auto"}:
            return self.model
        if self._resolved_model:
            return self._resolved_model
        models = self.list_models()
        self._resolved_model = models[0] if models else "local-model"
        return self._resolved_model

    def _prepare_messages(self, messages: list[ChatMessage], *, system_prompt: str | None = None) -> list[ChatMessage]:
        prepared = [dict(message) for message in messages]
        if system_prompt and not any(message.get("role") == "system" for message in prepared):
            prepared.insert(0, {"role": "system", "content": system_prompt})
        return prepared

    def _request_json(self, method: str, path: str, *, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                # LM Studio does not require a real OpenAI key locally, but
                # some OpenAI-compatible clients expect an Authorization header.
                "Authorization": "Bearer lm-studio",
            },
        )
        with self._urlopen(request, timeout=self.timeout_seconds) as response:
            body = response.read().decode("utf-8")
        return json.loads(body) if body else {}

    def _friendly_error(self, exc: Exception) -> str:
        if isinstance(exc, urllib.error.URLError):
            reason = getattr(exc, "reason", exc)
            return (
                f"Could not connect to LM Studio at {self.base_url}. "
                "Make sure LM Studio is open, a model is loaded, and the Local Server is running. "
                f"Details: {reason}"
            )
        if isinstance(exc, (socket.timeout, TimeoutError)):
            return f"LM Studio timed out after {self.timeout_seconds} seconds. The model may still be loading or responding slowly."
        return str(exc)
