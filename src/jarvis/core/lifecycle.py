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
from jarvis.memory.short_term import ShortTermMemory
from jarvis.providers.llm.base import LLMStreamCallback
from jarvis.providers.llm.factory import create_llm_provider
from jarvis.providers.tts.manager import TTSManager, format_tts_result
from jarvis.providers.tts.pipeline import SpokenResponsePipeline


class JarvisRuntime:
    """Boots the core Jarvis systems and handles user commands."""

    def __init__(self, *, project_root: str | Path | None = None, llm_provider: Any | None = None, tts_manager: TTSManager | None = None) -> None:
        self.config = JarvisConfig.from_project_root(project_root)
        self.events = EventBus()
        self.logger = JarvisLogger(self.config.logs_dir)
        self.registry = AgentRegistry()
        self.llm_provider = llm_provider or create_llm_provider(self.config)
        self.tts_manager = tts_manager or TTSManager(self.config, events=self.events)
        self.spoken_pipeline = SpokenResponsePipeline(
            self.tts_manager,
            events=self.events,
            chunk_max_chars=getattr(self.config, "tts_auto_speak_chunk_chars", 320),
            queue_max_size=getattr(self.config, "tts_queue_max_size", 12),
            play_audio=True,
        )
        self.router: JarvisRouter | None = None
        self.short_term_memory = ShortTermMemory(
            enabled=getattr(self.config, "memory_short_term_enabled", True),
            max_turns=getattr(self.config, "memory_short_term_max_turns", 20),
            max_chars=getattr(self.config, "memory_short_term_max_chars", 12000),
            inject_last_turns=getattr(self.config, "memory_short_term_inject_last_turns", 8),
            persist_path=self.config.data_dir / "conversations" / "short_term_session.json",
            autosave=getattr(self.config, "memory_short_term_autosave", False),
        )
        self.started = False
        self.last_timing: TurnTimer | None = None

        self.events.subscribe("*", lambda event: self.logger.log_event(event.event_type, source=event.source, message=event.message, data=event.data))

    def boot(self) -> JarvisResult:
        self.events.emit("jarvis.boot_started", source="lifecycle", message="Jarvis boot started.")
        self.registry.load_builtin_agents()
        self.router = JarvisRouter(
            registry=self.registry,
            events=self.events,
            llm_provider=self.llm_provider,
            config=self.config,
            short_term_memory=self.short_term_memory,
        )
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
                "short_term_memory": self.short_term_memory.status(),
                "tts": {
                    "enabled": self.tts_manager.enabled,
                    "provider": self.tts_manager.provider_name,
                    "auto_speak": self.tts_manager.auto_speak,
                    "spoken_pipeline": {
                        "queue_max_size": self.spoken_pipeline.queue_max_size,
                        "chunk_max_chars": self.spoken_pipeline.chunk_max_chars,
                    },
                },
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
        self._record_short_term_turn(command, result, timing=timing)
        result.data["timing"] = timing.to_dict()
        self.last_timing = timing
        self.logger.log_result(result)
        return result

    def timing_last(self) -> str:
        """Return a readable summary for the most recent command turn."""
        return format_timing_summary(self.last_timing)


    def memory_status(self) -> str:
        """Return user-facing short-term memory status."""
        return self.short_term_memory.format_status()

    def memory_last(self, limit: int = 5) -> str:
        """Return recent short-term memory turns."""
        return self.short_term_memory.format_last(limit=limit)

    def memory_clear(self) -> str:
        """Clear short-term memory and return a short confirmation."""
        removed = self.short_term_memory.clear()
        self.events.emit(
            "memory.short_term_cleared",
            source="lifecycle",
            message="Short-term memory cleared.",
            data={"removed_turns": removed},
        )
        return f"Short-term memory cleared. Removed {removed} turn(s)."

    def tts_status(self) -> str:
        """Return user-facing TTS status and provider diagnostics."""
        return self.tts_manager.status()

    def tts_providers(self) -> str:
        """Return the configured TTS provider chain."""
        return self.tts_manager.providers_summary()

    def tts_say(self, text: str, *, play_audio: bool | None = None) -> str:
        """Generate speech for text with the configured TTS provider chain."""
        result = self.tts_manager.say(text, play_audio=play_audio)
        return format_tts_result(result)

    def tts_test(self, *, play_audio: bool | None = None) -> str:
        """Generate a short test phrase through the TTS provider chain."""
        phrase = "Hello sir. Jarvis voice output is connected."
        result = self.tts_manager.say(phrase, play_audio=play_audio if play_audio is not None else getattr(self.config, "tts_playback", False))
        return format_tts_result(result)

    def tts_play_last(self) -> str:
        """Play the most recently generated TTS output, if available."""
        return format_tts_result(self.tts_manager.play_last())

    def tts_playback_on(self) -> str:
        """Enable audio playback for this runtime session."""
        self.tts_manager.set_playback(True)
        return "TTS playback is on for this runtime session. Generated WAV files will be played when possible."

    def tts_playback_off(self) -> str:
        """Disable audio playback for this runtime session."""
        self.tts_manager.set_playback(False)
        return "TTS playback is off for this runtime session. Jarvis will keep generating WAV files without playing them."

    def tts_reference_status(self) -> str:
        """Return legacy XTTS speaker reference setup status."""
        status = self.tts_manager.speaker_reference_status()
        lines = [
            "XTTS speaker reference status:",
            "- default Jarvis provider is now Kokoro; XTTS is experimental/personal-only and disabled unless explicitly selected.",
            f"- ready: {status['ready']}",
            f"- path: {status['path'] or '(not configured)'}",
            f"- message: {status['message']}",
            "- default import target: " + str(self.tts_manager.default_reference_path()),
        ]
        return "\n".join(lines)

    def tts_reference_set(self, path: str, *, import_to_default: bool = False) -> str:
        """Set or import the XTTS speaker reference WAV for this runtime session."""
        result = self.tts_manager.set_speaker_wav(path, copy_to_default=import_to_default)
        lines = [format_tts_result(result)]
        if result.success:
            status = self.tts_manager.speaker_reference_status()
            lines.append(f"Reference ready: {status['ready']} ({status['message']})")
        return "\n".join(lines)

    def tts_debug_last(self) -> str:
        """Return detailed provider-attempt diagnostics for the last TTS request."""
        return self.tts_manager.format_debug_last()

    def tts_queue_status(self) -> str:
        """Return spoken response queue diagnostics."""
        return self.spoken_pipeline.status()

    def tts_stop(self) -> str:
        """Stop current/pending spoken response output as much as possible."""
        removed = self.spoken_pipeline.stop(clear_pending=True)
        return f"Stopped spoken response output. Cleared {removed} pending chunk(s)."

    def tts_xtts_test(self, *, play_audio: bool | None = None) -> str:
        """Test experimental XTTS directly without falling back, so failures are visible."""
        phrase = "Hello sir. This is a direct experimental XTTS voice test."
        result = self.tts_manager.say(
            phrase,
            play_audio=play_audio if play_audio is not None else getattr(self.config, "tts_playback", False),
            provider_override="xtts",
            allow_fallback=False,
        )
        return format_tts_result(result)

    def tts_voice_list(self) -> str:
        """List known voices for the active TTS provider."""
        if self.tts_manager.provider_name == "kokoro":
            return self.tts_manager.format_kokoro_voices()
        return self.tts_manager.format_voice_profiles()

    def tts_voice_current(self) -> str:
        """Show the active voice for the active TTS provider."""
        if self.tts_manager.provider_name == "kokoro":
            return self.tts_manager.format_kokoro_current_voice()
        return self.tts_manager.format_current_voice()

    def tts_voice_import(self, voice_name: str, path: str, *, activate: bool = True) -> str:
        """Import a named experimental XTTS voice profile."""
        result = self.tts_manager.import_voice_profile(voice_name, path, activate=activate)
        return format_tts_result(result)

    def tts_voice_use(self, voice_name: str) -> str:
        """Switch the active voice for the active TTS provider."""
        if self.tts_manager.provider_name == "kokoro":
            result = self.tts_manager.set_kokoro_voice(voice_name)
        else:
            result = self.tts_manager.use_voice_profile(voice_name)
        return format_tts_result(result)

    def tts_voice_delete(self, voice_name: str) -> str:
        """Delete a named experimental XTTS voice profile, or explain Kokoro voices are built-in."""
        if self.tts_manager.provider_name == "kokoro":
            return "Kokoro voices are built into the provider and cannot be deleted from Jarvis. Use 'tts voice use <voice_id>' to switch voices."
        result = self.tts_manager.delete_voice_profile(voice_name)
        return format_tts_result(result)

    def tts_voice_test(self, voice_name: str | None = None, *, play_audio: bool | None = None) -> str:
        """Test a specific voice on the active TTS provider with no fallback."""
        selected_voice = voice_name or (self.tts_manager.kokoro_voice if self.tts_manager.provider_name == "kokoro" else self.tts_manager.voice_name)
        phrase = f"Hello sir. This is the {selected_voice} voice."
        provider = "kokoro" if self.tts_manager.provider_name == "kokoro" else "xtts"
        result = self.tts_manager.say(
            phrase,
            play_audio=play_audio if play_audio is not None else getattr(self.config, "tts_playback", False),
            voice_name=selected_voice,
            provider_override=provider,
            allow_fallback=False,
        )
        return format_tts_result(result)

    def tts_say_as(self, voice_name: str, text: str, *, play_audio: bool | None = None) -> str:
        """Generate speech using a specific voice on the active provider without changing the active voice."""
        provider = "kokoro" if self.tts_manager.provider_name == "kokoro" else "xtts"
        result = self.tts_manager.say(text, play_audio=play_audio, voice_name=voice_name, provider_override=provider, allow_fallback=False)
        return format_tts_result(result)

    def create_spoken_stream(self, display_callback=None):
        """Create a stream callback adapter for live spoken responses."""
        enabled = bool(self.tts_manager.enabled and self.tts_manager.auto_speak)
        return self.spoken_pipeline.create_stream_adapter(display_callback, enabled=enabled)

    def voice_status(self) -> str:
        """Return combined TTS and spoken pipeline status."""
        return self.tts_manager.status() + "\n\n" + self.spoken_pipeline.status()

    def voice_on(self) -> str:
        """Enable automatic voice output and playback for successful CLI chat responses."""
        self.tts_manager.set_auto_speak(True)
        self.tts_manager.set_playback(True)
        return (
            "Voice auto-speak and playback are on for this runtime session. "
            "Normal chat responses will be sent to the spoken response queue while text streams. "
            "Use 'voice off' or 'tts stop' to disable/stop it."
        )

    def voice_off(self) -> str:
        """Disable automatic voice output for CLI chat responses."""
        self.tts_manager.set_auto_speak(False)
        self.tts_manager.set_playback(False)
        removed = self.spoken_pipeline.stop(clear_pending=True)
        return f"Voice auto-speak and playback are off for this runtime session. Cleared {removed} pending speech chunk(s)."

    def _record_short_term_turn(self, command: str, result: JarvisResult, *, timing: TurnTimer | None = None) -> None:
        """Record normal LLM chat turns after the assistant response is ready."""
        if not result.success or result.action != "llm_chat":
            return
        if not getattr(self.config, "memory_short_term_enabled", True):
            return
        stored = self.short_term_memory.add_turn(
            user=command,
            assistant=result.message,
            agent_name=result.agent_name,
            action=result.action,
            success=result.success,
            metadata={
                "intent": result.data.get("intent"),
                "llm_model": result.data.get("llm_model"),
                "prompt_mode": result.data.get("prompt_mode"),
            },
        )
        if stored is None:
            return
        if timing is not None:
            timing.mark("memory.short_term_turn_saved", turns=len(self.short_term_memory.turns))
        self.events.emit(
            "memory.short_term_saved",
            source="lifecycle",
            message="Short-term conversation turn saved.",
            data={"turns": len(self.short_term_memory.turns), "session_id": self.short_term_memory.session_id},
        )

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
            f"- short-term memory: {'enabled' if getattr(self.config, 'memory_short_term_enabled', True) else 'disabled'}",
            f"- short-term memory turns: {len(self.short_term_memory.turns)} / {self.short_term_memory.max_turns}",
            f"- short-term injected turns: {self.short_term_memory.inject_last_turns}",
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
