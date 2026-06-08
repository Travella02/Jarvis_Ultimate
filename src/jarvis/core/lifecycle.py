"""Jarvis runtime boot/lifecycle helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.agents.conversation_agent.prompts import get_prompt_stats, get_system_prompt, normalize_prompt_mode
from jarvis.brain.router import JarvisRouter
from jarvis.core.config import JarvisConfig
from jarvis.core.events import EventBus
from jarvis.core.logging import JarvisLogger
from jarvis.core.registry import AgentRegistry
from jarvis.core.result import JarvisResult
from jarvis.core.timing import TurnTimer, format_timing_summary
from jarvis.providers.llm.base import LLMStreamCallback
from jarvis.providers.llm.factory import create_llm_provider


class JarvisRuntime:
    """Boots the core Jarvis systems and handles user commands."""

    def __init__(self, *, project_root: str | Path | None = None, llm_provider: Any | None = None) -> None:
        self.config = JarvisConfig.from_project_root(project_root)
        self.events = EventBus()
        self.logger = JarvisLogger(self.config.logs_dir)
        self.registry = AgentRegistry()
        self.llm_provider = llm_provider or create_llm_provider(self.config)
        self.router: JarvisRouter | None = None
        self.started = False
        self.last_timing: TurnTimer | None = None

        self.events.subscribe("*", lambda event: self.logger.log_event(event.event_type, source=event.source, message=event.message, data=event.data))

    def boot(self) -> JarvisResult:
        self.events.emit("jarvis.boot_started", source="lifecycle", message="Jarvis boot started.")
        self.registry.load_builtin_agents()
        self.router = JarvisRouter(registry=self.registry, events=self.events, llm_provider=self.llm_provider, config=self.config)
        self.started = True
        agent_names = self.registry.names(enabled_only=True)
        result = JarvisResult.ok(
            f"Jarvis 3 is online. Registered {len(agent_names)} agents.",
            agent_name="lifecycle",
            action="boot",
            data={
                "agents": agent_names,
                "llm_provider": getattr(self.llm_provider, "provider_name", "unknown"),
                "llm_model": getattr(self.llm_provider, "model", "unknown"),
                "llm_streaming": getattr(self.llm_provider, "streaming_enabled", False),
            },
        )
        self.logger.log_result(result)
        self.events.emit("jarvis.boot_finished", source="lifecycle", message="Jarvis boot finished.", data=result.data)
        return result

    def handle_command(self, command: str, *, stream_callback: LLMStreamCallback | None = None) -> JarvisResult:
        if not self.started:
            self.boot()
        if self.router is None:
            return JarvisResult.fail("Jarvis router failed to initialize.", agent_name="lifecycle", action="handle_command")

        timing = TurnTimer(command=command)
        timing.mark("runtime.handle_command_start", stream_callback=stream_callback is not None)
        result = self.router.handle(command, timing=timing, stream_callback=stream_callback)
        timing.mark("runtime.handle_command_finished", success=result.success, action=result.action, streamed=result.data.get("streamed_output"))
        result.data["timing"] = timing.to_dict()
        self.last_timing = timing
        self.logger.log_result(result)
        return result

    def timing_last(self) -> str:
        """Return a readable summary for the most recent command turn."""
        return format_timing_summary(self.last_timing)

    def prompt_diagnostics(self) -> str:
        """Return current LLM prompt/config diagnostics for the CLI."""
        stats = get_prompt_stats(getattr(self.config, "conversation_prompt_mode", "normal"))
        provider_name = getattr(self.llm_provider, "provider_name", "unknown")
        provider_model = getattr(self.llm_provider, "model", "unknown")
        streaming = getattr(self.llm_provider, "streaming_enabled", False)
        base_url = str(getattr(self.config, "llm_base_url", "unknown"))
        native_base_url = str(getattr(self.llm_provider, "native_base_url", getattr(self.config, "llm_native_base_url", "unknown")))
        lines = [
            "LLM prompt/config diagnostics:",
            f"- provider: {provider_name}",
            f"- model: {provider_model}",
            f"- base URL: {base_url}",
            f"- API mode: {getattr(self.llm_provider, 'api_mode', getattr(self.config, 'llm_api_mode', 'openai'))}",
            f"- native base URL: {native_base_url}",
            f"- reasoning/thinking: {getattr(self.llm_provider, 'reasoning', getattr(self.config, 'llm_reasoning', 'auto'))}",
            f"- context length override: {getattr(self.llm_provider, 'context_length', getattr(self.config, 'llm_context_length', None)) or 'default'}",
            f"- streaming: {'enabled' if streaming else 'disabled'}",
            f"- temperature: {getattr(self.config, 'llm_temperature', 'unknown')}",
            f"- max tokens: {getattr(self.config, 'llm_max_tokens', 'unknown')}",
            f"- conversation prompt mode: {stats['mode']}",
            f"- system prompt enabled: {stats['enabled']}",
            f"- system prompt size: {stats['chars']} chars, {stats['words']} words, {stats['lines']} lines",
            f"- benchmark max tokens: {getattr(self.config, 'llm_benchmark_max_tokens', 'unknown')}",
        ]
        lines.extend(self._loopback_warnings(base_url=base_url, native_base_url=native_base_url))
        return "\n".join(lines)

    def benchmark_llm(self, *, prompt_mode: str | None = None, api_mode: str | None = None, reasoning: str | None = None) -> str:
        """Run a direct LLM benchmark that bypasses router/agent structure.

        ``api_mode`` and ``reasoning`` temporarily override LM Studio provider
        settings for one benchmark turn. That lets the CLI compare the
        OpenAI-compatible path against LM Studio's native API without changing
        the user's .env file first.
        """
        selected_mode = normalize_prompt_mode(prompt_mode or getattr(self.config, "conversation_prompt_mode", "normal"))
        system_prompt = get_system_prompt(selected_mode)
        prompt = getattr(self.config, "llm_benchmark_prompt", "Reply with exactly one short sentence saying you are ready.")
        max_tokens = int(getattr(self.config, "llm_benchmark_max_tokens", 64))
        selected_api_mode = self._normalize_api_mode(api_mode or getattr(self.llm_provider, "api_mode", getattr(self.config, "llm_api_mode", "openai")))
        selected_reasoning = self._normalize_reasoning(reasoning or getattr(self.llm_provider, "reasoning", getattr(self.config, "llm_reasoning", "auto")))
        timing = TurnTimer(command=f"benchmark llm {selected_mode} {selected_api_mode} {selected_reasoning}")
        chunks: list[str] = []

        def collect_chunk(chunk: str) -> None:
            chunks.append(chunk)

        timing.mark(
            "diagnostic.direct_lm_benchmark_start",
            prompt_mode=selected_mode,
            benchmark_prompt_chars=len(prompt),
            system_prompt_chars=len(system_prompt or ""),
            max_tokens=max_tokens,
            api_mode=selected_api_mode,
            reasoning=selected_reasoning,
        )

        old_api_mode = getattr(self.llm_provider, "api_mode", None)
        old_reasoning = getattr(self.llm_provider, "reasoning", None)
        if old_api_mode is not None:
            setattr(self.llm_provider, "api_mode", selected_api_mode)
        if old_reasoning is not None:
            setattr(self.llm_provider, "reasoning", selected_reasoning)
        try:
            response = self.llm_provider.chat(
            [{"role": "user", "content": prompt}],
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            timing=timing,
                stream_callback=collect_chunk,
                stream=True,
            )
        finally:
            if old_api_mode is not None:
                setattr(self.llm_provider, "api_mode", old_api_mode)
            if old_reasoning is not None:
                setattr(self.llm_provider, "reasoning", old_reasoning)
        timing.mark(
            "diagnostic.direct_lm_benchmark_finished",
            success=response.success,
            chars=len(response.content),
            chunks=len(chunks),
            provider=response.provider,
            model=response.model,
        )
        self.last_timing = timing

        lines = [
            f"Direct LLM benchmark complete. Success: {response.success}.",
            "This bypasses the router and Conversation Agent so you can compare it against a normal Jarvis message.",
            f"Prompt mode: {selected_mode}. API mode: {selected_api_mode}. Reasoning: {selected_reasoning}. Max tokens: {max_tokens}. Chunks: {len(chunks)}. Response chars: {len(response.content)}.",
        ]
        if response.content:
            preview = response.content.replace("\n", " ")[:160]
            lines.append(f"Response preview: {preview}")
        if response.error:
            lines.append(f"Error: {response.error}")
        lines.append("")
        lines.extend(timing.summary_lines())
        return "\n".join(lines)


    def _loopback_warnings(self, *, base_url: str, native_base_url: str) -> list[str]:
        """Warn when a local LM Studio URL uses localhost instead of 127.0.0.1.

        On Tanner's Windows setup, localhost added about two seconds before the
        LM Studio API stream opened. 127.0.0.1 avoids that name-resolution path.
        """
        warnings: list[str] = []
        if "localhost" in base_url.lower():
            warnings.append("- warning: base URL uses localhost; use http://127.0.0.1:1234/v1 for faster local LM Studio calls on Windows.")
        if "localhost" in native_base_url.lower():
            warnings.append("- warning: native base URL uses localhost; use http://127.0.0.1:1234 for native diagnostics.")
        return warnings


    def _normalize_api_mode(self, value: str | None) -> str:
        text = str(value or "openai").strip().lower().replace("-", "_")
        if text in {"native", "lmstudio_native", "lm_studio_native", "api_v1"}:
            return "native"
        return "openai"

    def _normalize_reasoning(self, value: str | None) -> str:
        text = str(value or "auto").strip().lower().replace("-", "_")
        if text in {"off", "low", "medium", "high", "on"}:
            return text
        return "auto"
