"""LM Studio LLM provider.

This provider can talk to LM Studio in two request modes:

* ``openai``: LM Studio's OpenAI-compatible ``/v1/chat/completions`` API.
* ``native``: LM Studio's native ``/api/v1/chat`` API, which can expose
  request-level options such as reasoning and context length.

Jarvis defaults to the OpenAI-compatible path for compatibility. The native
mode is available for diagnostics and speed testing because LM Studio's own UI
may use native settings such as reasoning/thinking off.
"""

from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any, Callable, Iterable

from jarvis.providers.llm.base import ChatMessage, LLMResponse, LLMStreamCallback


UrlOpen = Callable[..., Any]

_REASONING_VALUES = {"off", "low", "medium", "high", "on"}
_DEFAULT_REASONING_VALUES = {"", "auto", "default", "none"}


class LMStudioProvider:
    provider_name = "lm_studio"

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:1234/v1",
        model: str = "auto",
        timeout_seconds: float = 90.0,
        temperature: float = 0.7,
        max_tokens: int = 512,
        auto_model_name: str = "local-model",
        resolve_auto_model: bool = False,
        streaming_enabled: bool = True,
        api_mode: str = "openai",
        native_base_url: str | None = None,
        reasoning: str = "auto",
        context_length: int | None = None,
        store_native_chats: bool = False,
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
        self.api_mode = self._normalize_api_mode(api_mode)
        self.native_base_url = (native_base_url.rstrip("/") if native_base_url else self._derive_native_base_url(self.base_url))
        self.reasoning = self._normalize_reasoning(reasoning)
        self.context_length = int(context_length) if context_length else None
        self.store_native_chats = store_native_chats
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
        self._mark(timing, "lm_studio.prepare_start", api_mode=self.api_mode)
        prepared_messages = self._prepare_messages(messages, system_prompt=system_prompt)
        model = self.resolve_model(timing=timing)
        should_stream = self._should_stream(stream=stream, stream_callback=stream_callback)
        effective_temperature = self.temperature if temperature is None else temperature
        effective_max_tokens = self.max_tokens if max_tokens is None else max_tokens
        api_mode = self._normalize_api_mode(self.api_mode)

        if api_mode == "native":
            payload = self._build_native_payload(
                prepared_messages,
                model=model,
                stream=should_stream,
                temperature=effective_temperature,
                max_tokens=effective_max_tokens,
            )
            path = "/api/v1/chat"
            request_base_url = self.native_base_url
        else:
            payload = self._build_openai_payload(
                prepared_messages,
                model=model,
                stream=should_stream,
                temperature=effective_temperature,
                max_tokens=effective_max_tokens,
            )
            path = "/chat/completions"
            request_base_url = self.base_url

        payload_bytes = len(json.dumps(payload).encode("utf-8"))
        message_stats = self._message_stats(prepared_messages)
        self._mark(
            timing,
            "lm_studio.prepare_finished",
            model=model,
            api_mode=api_mode,
            path=path,
            message_count=len(prepared_messages),
            stream=should_stream,
            payload_bytes=payload_bytes,
            prompt_chars=message_stats["total_chars"],
            system_chars=message_stats["system_chars"],
            user_chars=message_stats["user_chars"],
            assistant_chars=message_stats["assistant_chars"],
            temperature=effective_temperature,
            max_tokens=effective_max_tokens,
            reasoning=self.reasoning if api_mode == "native" else None,
            context_length=self.context_length if api_mode == "native" else None,
            native_base_url=request_base_url if api_mode == "native" else None,
        )

        try:
            if api_mode == "native":
                if should_stream:
                    return self._chat_native_stream(payload, model=model, timing=timing, stream_callback=stream_callback)
                raw = self._request_json(
                    "POST",
                    path,
                    payload=payload,
                    timing=timing,
                    timing_label="lm_studio",
                    base_url=request_base_url,
                    stream=False,
                )
                content = self._extract_native_content(raw)
                if not content:
                    return LLMResponse.fail("LM Studio native API returned an empty response.", provider=self.provider_name, model=model, raw=raw)
                return LLMResponse.ok(content.strip(), provider=self.provider_name, model=model, raw=raw)

            if should_stream:
                return self._chat_openai_stream(payload, model=model, timing=timing, stream_callback=stream_callback)
            raw = self._request_json(
                "POST",
                path,
                payload=payload,
                timing=timing,
                timing_label="lm_studio",
                base_url=request_base_url,
                stream=False,
            )
            content = raw.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                return LLMResponse.fail("LM Studio returned an empty response.", provider=self.provider_name, model=model, raw=raw)
            return LLMResponse.ok(content.strip(), provider=self.provider_name, model=model, raw=raw)
        except Exception as exc:
            return LLMResponse.fail(self._friendly_error(exc), provider=self.provider_name, model=model)

    def list_models(self, *, timing: Any | None = None) -> list[str]:
        try:
            raw = self._request_json("GET", "/models", timing=timing, timing_label="lm_studio.models", base_url=self.base_url, stream=False)
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

    def _build_openai_payload(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        stream: bool,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True
        return payload

    def _build_native_payload(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        stream: bool,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        input_value, system_prompt = self._native_input_and_system_prompt(messages)
        payload: dict[str, Any] = {
            "model": model,
            "input": input_value,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "store": self.store_native_chats,
        }
        if system_prompt:
            payload["system_prompt"] = system_prompt
        if stream:
            payload["stream"] = True
        if self.reasoning in _REASONING_VALUES:
            payload["reasoning"] = self.reasoning
        if self.context_length:
            payload["context_length"] = self.context_length
        return payload

    def _prepare_messages(self, messages: list[ChatMessage], *, system_prompt: str | None = None) -> list[ChatMessage]:
        prepared = [dict(message) for message in messages]
        if system_prompt and not any(message.get("role") == "system" for message in prepared):
            prepared.insert(0, {"role": "system", "content": system_prompt})
        return prepared

    def _native_input_and_system_prompt(self, messages: list[ChatMessage]) -> tuple[str | list[dict[str, str]], str]:
        system_parts: list[str] = []
        conversation_parts: list[dict[str, str]] = []
        last_user_content = ""

        for message in messages:
            role = str(message.get("role", "user")).lower()
            content = str(message.get("content", ""))
            if not content:
                continue
            if role == "system":
                system_parts.append(content)
                continue
            if role == "user":
                last_user_content = content
                conversation_parts.append({"type": "message", "content": content})
            else:
                # The native endpoint supports stateful chat, but Jarvis does not
                # use that yet. Prefix non-user messages so diagnostics do not
                # silently lose context when tests eventually include history.
                conversation_parts.append({"type": "message", "content": f"{role}: {content}"})

        if len(conversation_parts) == 1 and last_user_content:
            input_value: str | list[dict[str, str]] = last_user_content
        else:
            input_value = conversation_parts or ""
        return input_value, "\n\n".join(system_parts).strip()

    def _message_stats(self, messages: list[ChatMessage]) -> dict[str, int]:
        stats = {"total_chars": 0, "system_chars": 0, "user_chars": 0, "assistant_chars": 0, "other_chars": 0}
        for message in messages:
            role = str(message.get("role", "other")).lower()
            content = str(message.get("content", ""))
            char_count = len(content)
            stats["total_chars"] += char_count
            if role == "system":
                stats["system_chars"] += char_count
            elif role == "user":
                stats["user_chars"] += char_count
            elif role == "assistant":
                stats["assistant_chars"] += char_count
            else:
                stats["other_chars"] += char_count
        return stats

    def _should_stream(self, *, stream: bool | None, stream_callback: LLMStreamCallback | None) -> bool:
        if stream is not None:
            return bool(stream)
        return self.streaming_enabled and stream_callback is not None

    def _chat_openai_stream(
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

        for payload_text in self._request_stream(
            "POST",
            "/chat/completions",
            payload=payload,
            timing=timing,
            timing_label="lm_studio",
            base_url=self.base_url,
        ):
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
            delta = self._extract_openai_stream_delta(choice)
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
                raw={"streamed": True, "api_mode": "openai", "chunk_count": len(chunks), "bytes": byte_count},
            )
        return LLMResponse.ok(
            content,
            provider=self.provider_name,
            model=model,
            raw={"streamed": True, "api_mode": "openai", "chunk_count": len(chunks), "bytes": byte_count, "finish_reason": finish_reason},
        )

    def _chat_native_stream(
        self,
        payload: dict[str, Any],
        *,
        model: str,
        timing: Any | None,
        stream_callback: LLMStreamCallback | None,
    ) -> LLMResponse:
        chunks: list[str] = []
        byte_count = 0
        first_chunk_sent = False
        error_message: str | None = None
        final_result: dict[str, Any] | None = None
        reasoning_events = 0
        prompt_events = 0

        for event_name, payload_text in self._request_event_stream(
            "POST",
            "/api/v1/chat",
            payload=payload,
            timing=timing,
            timing_label="lm_studio",
            base_url=self.native_base_url,
        ):
            byte_count += len(payload_text.encode("utf-8"))
            try:
                raw_event = json.loads(payload_text)
            except json.JSONDecodeError:
                self._mark(timing, "lm_studio.native_stream_parse_skipped", event=event_name)
                continue

            event_type = str(raw_event.get("type") or event_name or "unknown")
            if event_type.startswith("prompt_processing"):
                prompt_events += 1
                self._mark(timing, f"lm_studio.{event_type.replace('.', '_')}")
            elif event_type.startswith("reasoning"):
                reasoning_events += 1
                if event_type in {"reasoning.start", "reasoning.end"}:
                    self._mark(timing, f"lm_studio.{event_type.replace('.', '_')}")
            elif event_type in {"chat.start", "message.start", "message.end"}:
                self._mark(timing, f"lm_studio.{event_type.replace('.', '_')}")

            if event_type == "message.delta":
                delta = str(raw_event.get("content", ""))
                if not delta:
                    continue
                if not first_chunk_sent:
                    first_chunk_sent = True
                    self._mark(timing, "lm_studio.first_chunk", chars=len(delta), native_event=event_type)
                chunks.append(delta)
                if stream_callback is not None:
                    stream_callback(delta)
            elif event_type == "error":
                error = raw_event.get("error", {})
                if isinstance(error, dict):
                    error_message = str(error.get("message") or error)
                else:
                    error_message = str(error)
                self._mark(timing, "lm_studio.native_error", message=error_message)
            elif event_type == "chat.end":
                final_result = raw_event.get("result") if isinstance(raw_event.get("result"), dict) else None
                self._mark(timing, "lm_studio.stream_done", native_event=event_type)
                self._mark_native_stats(timing, final_result)

        content = "".join(chunks).strip()
        if not content and final_result:
            content = self._extract_native_content(final_result).strip()
        self._mark(
            timing,
            "lm_studio.stream_collected",
            chunks=len(chunks),
            chars=len(content),
            api_mode="native",
            bytes=byte_count,
            prompt_events=prompt_events,
            reasoning_events=reasoning_events,
        )
        if not content:
            return LLMResponse.fail(
                error_message or "LM Studio native API returned an empty streamed response.",
                provider=self.provider_name,
                model=model,
                raw={"streamed": True, "api_mode": "native", "chunk_count": len(chunks), "bytes": byte_count, "result": final_result},
            )
        return LLMResponse.ok(
            content,
            provider=self.provider_name,
            model=model,
            raw={"streamed": True, "api_mode": "native", "chunk_count": len(chunks), "bytes": byte_count, "result": final_result},
        )

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        timing: Any | None = None,
        timing_label: str = "lm_studio",
        base_url: str | None = None,
        stream: bool = False,
    ) -> dict[str, Any]:
        url = f"{(base_url or self.base_url).rstrip('/')}{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = self._build_request(url, method=method, data=data)
        self._mark(timing, f"{timing_label}.request_start", method=method, path=path, stream=stream, payload_bytes=len(data or b""))
        try:
            with self._urlopen(request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
            self._mark(timing, f"{timing_label}.request_finished", method=method, path=path, bytes=len(body), stream=stream)
        except Exception:
            self._mark(timing, f"{timing_label}.request_failed", method=method, path=path, stream=stream)
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
        base_url: str | None = None,
    ) -> Iterable[str]:
        url = f"{(base_url or self.base_url).rstrip('/')}{path}"
        data = json.dumps(payload).encode("utf-8")
        request = self._build_request(url, method=method, data=data, accept="text/event-stream")
        self._mark(timing, f"{timing_label}.request_start", method=method, path=path, stream=True, payload_bytes=len(data))
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

    def _request_event_stream(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any],
        timing: Any | None = None,
        timing_label: str = "lm_studio",
        base_url: str | None = None,
    ) -> Iterable[tuple[str, str]]:
        url = f"{(base_url or self.native_base_url).rstrip('/')}{path}"
        data = json.dumps(payload).encode("utf-8")
        request = self._build_request(url, method=method, data=data, accept="text/event-stream")
        self._mark(timing, f"{timing_label}.request_start", method=method, path=path, stream=True, payload_bytes=len(data))
        failed = False
        try:
            with self._urlopen(request, timeout=self.timeout_seconds) as response:
                self._mark(timing, f"{timing_label}.stream_opened", method=method, path=path)
                try:
                    for event_name, payload_text in self._iter_sse_events(response):
                        yield event_name, payload_text
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
                # some compatible modes expect an Authorization header.
                "Authorization": "Bearer lm-studio",
            },
        )

    def _iter_stream_payloads(self, response: Any) -> Iterable[str]:
        """Yield parsed SSE data payloads from OpenAI-compatible streams."""
        for _event_name, payload_text in self._iter_sse_events(response):
            yield payload_text

    def _iter_sse_events(self, response: Any) -> Iterable[tuple[str, str]]:
        """Yield ``(event_name, data)`` pairs from an SSE response.

        LM Studio's OpenAI-compatible stream mostly uses data-only SSE lines,
        while the native API uses named events such as ``message.delta``. This
        parser supports both styles and also tolerates simple raw JSON lines in
        unit-test doubles.
        """
        line_source: Iterable[Any]
        try:
            line_source = iter(response)
        except TypeError:
            body = response.read()
            if isinstance(body, bytes):
                line_source = body.splitlines()
            else:
                line_source = str(body).splitlines()

        event_name = "message"
        data_parts: list[str] = []

        def flush() -> tuple[str, str] | None:
            nonlocal event_name, data_parts
            if not data_parts:
                return None
            item = (event_name, "\n".join(data_parts).strip())
            event_name = "message"
            data_parts = []
            return item

        for raw_line in line_source:
            line = raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else str(raw_line)
            line = line.rstrip("\r\n")
            if not line.strip():
                item = flush()
                if item:
                    yield item
                continue
            stripped = line.strip()
            if stripped.startswith("event:"):
                event_name = stripped.removeprefix("event:").strip() or "message"
            elif stripped.startswith("data:"):
                data = stripped.removeprefix("data:").strip()
                data_parts.append(data)
                # Test fakes often omit the blank line delimiter. OpenAI-style
                # data-only events should still be yielded one line at a time.
                if event_name == "message" and (data == "[DONE]" or data.startswith("{") or data.startswith("[")):
                    item = flush()
                    if item:
                        yield item
            elif stripped.startswith("{"):
                item = flush()
                if item:
                    yield item
                yield event_name, stripped

        item = flush()
        if item:
            yield item

    def _extract_openai_stream_delta(self, choice: dict[str, Any]) -> str:
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

    def _extract_native_content(self, raw: dict[str, Any]) -> str:
        output = raw.get("output", [])
        if isinstance(output, list):
            parts: list[str] = []
            for item in output:
                if isinstance(item, dict) and item.get("type") == "message" and item.get("content"):
                    parts.append(str(item.get("content")))
            if parts:
                return "".join(parts)
        message = raw.get("message")
        if isinstance(message, str):
            return message
        content = raw.get("content")
        if isinstance(content, str):
            return content
        return ""

    def _mark_native_stats(self, timing: Any | None, final_result: dict[str, Any] | None) -> None:
        if not final_result:
            return
        stats = final_result.get("stats")
        if not isinstance(stats, dict):
            return
        self._mark(
            timing,
            "lm_studio.native_stats",
            input_tokens=stats.get("input_tokens"),
            total_output_tokens=stats.get("total_output_tokens"),
            reasoning_output_tokens=stats.get("reasoning_output_tokens"),
            tokens_per_second=stats.get("tokens_per_second"),
            time_to_first_token_seconds=stats.get("time_to_first_token_seconds"),
        )

    def _normalize_api_mode(self, value: str | None) -> str:
        text = str(value or "openai").strip().lower().replace("-", "_")
        if text in {"native", "lmstudio_native", "lm_studio_native", "api_v1"}:
            return "native"
        return "openai"

    def _normalize_reasoning(self, value: str | None) -> str:
        text = str(value or "auto").strip().lower().replace("-", "_")
        if text in _REASONING_VALUES:
            return text
        if text in _DEFAULT_REASONING_VALUES:
            return "auto"
        return "auto"

    def _derive_native_base_url(self, base_url: str) -> str:
        text = base_url.rstrip("/")
        if text.endswith("/api/v1"):
            return text[: -len("/api/v1")]
        if text.endswith("/v1"):
            return text[: -len("/v1")]
        return text

    def _mark(self, timing: Any | None, name: str, **data: Any) -> None:
        if timing is not None and hasattr(timing, "mark"):
            timing.mark(name, **data)

    def _friendly_error(self, exc: Exception) -> str:
        if isinstance(exc, urllib.error.URLError):
            reason = getattr(exc, "reason", exc)
            target_url = self.native_base_url if self._normalize_api_mode(self.api_mode) == "native" else self.base_url
            return (
                f"Could not connect to LM Studio at {target_url}. "
                "Make sure LM Studio is open, a model is loaded, and the Local Server is running. "
                f"Details: {reason}"
            )
        if isinstance(exc, (socket.timeout, TimeoutError)):
            return f"LM Studio timed out after {self.timeout_seconds} seconds. The model may still be loading or responding slowly."
        return str(exc)
