"""LM Studio OpenAI-compatible LLM provider.

This provider talks to LM Studio's local OpenAI-compatible API, normally at:

    http://localhost:1234/v1

Jarvis 0.0.4 removed the avoidable pre-chat /v1/models lookup. Jarvis 0.0.5
adds streamed chat completions so clients such as the CLI can show tokens as
soon as LM Studio sends them instead of waiting for the full answer.
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any, Callable, Iterable

from jarvis.providers.llm.base import ChatMessage, LLMResponse, LLMStreamCallback


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
        streaming_enabled: bool = True,
        urlopen: UrlOpen | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model or "auto"
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.auto_model_name = auto_model_name or "local-model"
        self.resolve_auto_model = resolve_auto_model
        self.streaming_enabled = streaming_enabled
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
        stream_callback: LLMStreamCallback | None = None,
        stream: bool | None = None,
    ) -> LLMResponse:
        self._mark(timing, "lm_studio.prepare_start")
        prepared_messages = self._prepare_messages(messages, system_prompt=system_prompt)
        model = self.resolve_model(timing=timing)
        should_stream = self._should_stream(stream=stream, stream_callback=stream_callback)
        payload = {
            "model": model,
            "messages": prepared_messages,
            "temperature": self.temperature if temperature is None else temperature,
            "max_tokens": self.max_tokens if max_tokens is None else max_tokens,
        }
        if should_stream:
            payload["stream"] = True
        self._mark(
            timing,
            "lm_studio.prepare_finished",
            model=model,
            message_count=len(prepared_messages),
            stream=should_stream,
        )

        try:
            if should_stream:
                return self._chat_stream(payload, model=model, timing=timing, stream_callback=stream_callback)
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

    def _should_stream(self, *, stream: bool | None, stream_callback: LLMStreamCallback | None) -> bool:
        if stream is not None:
            return bool(stream)
        return self.streaming_enabled and stream_callback is not None

    def _chat_stream(
        self,
        payload: dict[str, Any],
        *,
        model: str,
        timing: Any | None,
        stream_callback: LLMStreamCallback | None,
    ) -> LLMResponse:
        chunks: list[str] = []
        finish_reason: str | None = None
        byte_count = 0
        first_chunk_sent = False

        for payload_text in self._request_stream("POST", "/chat/completions", payload=payload, timing=timing, timing_label="lm_studio"):
            byte_count += len(payload_text.encode("utf-8"))
            if payload_text == "[DONE]":
                self._mark(timing, "lm_studio.stream_done")
                break
            try:
                raw_chunk = json.loads(payload_text)
            except json.JSONDecodeError:
                self._mark(timing, "lm_studio.stream_parse_skipped")
                continue

            choice = raw_chunk.get("choices", [{}])[0]
            finish_reason = choice.get("finish_reason") or finish_reason
            delta = self._extract_stream_delta(choice)
            if not delta:
                continue

            if not first_chunk_sent:
                first_chunk_sent = True
                self._mark(timing, "lm_studio.first_chunk", chars=len(delta))
            chunks.append(delta)
            if stream_callback is not None:
                stream_callback(delta)

        content = "".join(chunks).strip()
        self._mark(timing, "lm_studio.stream_collected", chunks=len(chunks), chars=len(content), finish_reason=finish_reason)
        if not content:
            return LLMResponse.fail(
                "LM Studio returned an empty streamed response.",
                provider=self.provider_name,
                model=model,
                raw={"streamed": True, "chunk_count": len(chunks), "bytes": byte_count},
            )
        return LLMResponse.ok(
            content,
            provider=self.provider_name,
            model=model,
            raw={"streamed": True, "chunk_count": len(chunks), "bytes": byte_count, "finish_reason": finish_reason},
        )

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
        request = self._build_request(url, method=method, data=data)
        self._mark(timing, f"{timing_label}.request_start", method=method, path=path, stream=False)
        try:
            with self._urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
            self._mark(timing, f"{timing_label}.request_finished", method=method, path=path, bytes=len(body), stream=False)
        except Exception:
            self._mark(timing, f"{timing_label}.request_failed", method=method, path=path, stream=False)
            raise
        return json.loads(body) if body else {}

    def _request_stream(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any],
        timing: Any | None = None,
        timing_label: str = "lm_studio",
    ) -> Iterable[str]:
        url = f"{self.base_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        request = self._build_request(url, method=method, data=data, accept="text/event-stream")
        self._mark(timing, f"{timing_label}.request_start", method=method, path=path, stream=True)
        failed = False
        try:
            with self._urlopen(request, timeout=self.timeout_seconds) as response:
                self._mark(timing, f"{timing_label}.stream_opened", method=method, path=path)
                try:
                    for payload_text in self._iter_stream_payloads(response):
                        yield payload_text
                finally:
                    if not failed:
                        self._mark(timing, f"{timing_label}.request_finished", method=method, path=path, stream=True)
        except Exception:
            failed = True
            self._mark(timing, f"{timing_label}.request_failed", method=method, path=path, stream=True)
            raise

    def _build_request(self, url: str, *, method: str, data: bytes | None, accept: str = "application/json") -> urllib.request.Request:
        return urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={
                "Content-Type": "application/json",
                "Accept": accept,
                # LM Studio does not require a real OpenAI key locally, but
                # some OpenAI-compatible clients expect an Authorization header.
                "Authorization": "Bearer lm-studio",
            },
        )

    def _iter_stream_payloads(self, response: Any) -> Iterable[str]:
        """Yield parsed SSE data payloads from LM Studio's streaming response."""
        line_source: Iterable[Any]
        try:
            line_source = iter(response)
        except TypeError:
            body = response.read()
            if isinstance(body, bytes):
                line_source = body.splitlines()
            else:
                line_source = str(body).splitlines()

        for raw_line in line_source:
            line = raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else str(raw_line)
            line = line.strip()
            if not line:
                continue
            if line.startswith("data:"):
                yield line.removeprefix("data:").strip()
            elif line.startswith("{"):
                # Some test doubles or compatible servers may provide raw JSON
                # lines instead of strict SSE data lines.
                yield line

    def _extract_stream_delta(self, choice: dict[str, Any]) -> str:
        delta = choice.get("delta")
        if isinstance(delta, dict):
            content = delta.get("content")
            if content:
                return str(content)
        message = choice.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if content:
                return str(content)
        text = choice.get("text")
        return str(text) if text else ""

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
