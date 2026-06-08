"""LM Studio OpenAI-compatible LLM provider.

This provider talks to LM Studio's local OpenAI-compatible API, normally at:

    http://localhost:1234/v1

Jarvis 0.0.4 keeps the provider dependency-free and adds latency timing marks.
The default model="auto" path no longer calls /v1/models before every first
chat request. That avoids a noticeable pre-LLM delay on some local setups.
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
        auto_model_name: str = "local-model",
        resolve_auto_model: bool = False,
        urlopen: UrlOpen | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model or "auto"
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.auto_model_name = auto_model_name or "local-model"
        self.resolve_auto_model = resolve_auto_model
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
        timing: Any | None = None,
    ) -> LLMResponse:
        self._mark(timing, "lm_studio.prepare_start")
        prepared_messages = self._prepare_messages(messages, system_prompt=system_prompt)
        model = self.resolve_model(timing=timing)
        payload = {
            "model": model,
            "messages": prepared_messages,
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": self.max_tokens if max_tokens is None else max_tokens,
        }
        self._mark(timing, "lm_studio.prepare_finished", model=model, message_count=len(prepared_messages))

        try:
            raw = self._request_json("POST", "/chat/completions", payload=payload, timing=timing, timing_label="lm_studio")
            content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                return LLMResponse.fail("LM Studio returned an empty response.", provider=self.provider_name, model=model, raw=raw)
            return LLMResponse.ok(content.strip(), provider=self.provider_name, model=model, raw=raw)
        except Exception as exc:
            return LLMResponse.fail(self._friendly_error(exc), provider=self.provider_name, model=model)

    def list_models(self, *, timing: Any | None = None) -> list[str]:
        try:
            raw = self._request_json("GET", "/models", timing=timing, timing_label="lm_studio.models")
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

    def resolve_model(self, *, timing: Any | None = None) -> str:
        """Resolve the model id without a network lookup unless explicitly enabled."""
        if self.model.lower() not in {"", "auto"}:
            self._mark(timing, "lm_studio.model_resolved", mode="configured", model=self.model)
            return self.model

        if self._resolved_model:
            self._mark(timing, "lm_studio.model_resolved", mode="cached", model=self._resolved_model)
            return self._resolved_model

        if not self.resolve_auto_model:
            self._resolved_model = self.auto_model_name
            self._mark(timing, "lm_studio.model_resolved", mode="fast_path", model=self._resolved_model)
            return self._resolved_model

        self._mark(timing, "lm_studio.model_lookup_start")
        models = self.list_models(timing=timing)
        self._resolved_model = models[0] if models else self.auto_model_name
        self._mark(timing, "lm_studio.model_resolved", mode="lookup", model=self._resolved_model, model_count=len(models))
        return self._resolved_model

    def _prepare_messages(self, messages: list[ChatMessage], *, system_prompt: str | None = None) -> list[ChatMessage]:
        prepared = [dict(message) for message in messages]
        if system_prompt and not any(message.get("role") == "system" for message in prepared):
            prepared.insert(0, {"role": "system", "content": system_prompt})
        return prepared

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        timing: Any | None = None,
        timing_label: str = "lm_studio",
    ) -> dict[str, Any]:
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
        self._mark(timing, f"{timing_label}.request_start", method=method, path=path)
        try:
            with self._urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
            self._mark(timing, f"{timing_label}.request_finished", method=method, path=path, bytes=len(body))
        except Exception:
            self._mark(timing, f"{timing_label}.request_failed", method=method, path=path)
            raise
        return json.loads(body) if body else {}

    def _mark(self, timing: Any | None, name: str, **data: Any) -> None:
        if timing is not None and hasattr(timing, "mark"):
            timing.mark(name, **data)

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
