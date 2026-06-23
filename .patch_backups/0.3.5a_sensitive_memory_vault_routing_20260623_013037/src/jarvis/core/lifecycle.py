"""Jarvis runtime boot/lifecycle helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import itertools

from jarvis.agents.conversation_agent.prompts import get_prompt_stats, get_system_prompt, normalize_prompt_mode
from jarvis.brain.router import JarvisRouter
from jarvis.abilities.registry import AbilityRegistry
from jarvis.core.config import JarvisConfig
from jarvis.core.events import EventBus
from jarvis.core.logging import JarvisLogger
from jarvis.core.registry import AgentRegistry
from jarvis.core.result import JarvisResult
from jarvis.core.timing import TurnTimer, format_timing_summary
from jarvis.memory.short_term import ShortTermMemory
from jarvis.memory.long_term import LongTermMemoryStore
from jarvis.memory.always_on import ChatArchiveStore, MemoryAutoCaptureEngine, MemoryCandidateStore, MemoryMaintenance, ShortTermFactStore
from jarvis.memory.entities import EntityMemoryStore
from jarvis.memory.preferences import MemoryPreferenceStore
from jarvis.providers.llm.base import LLMStreamCallback
from jarvis.providers.llm.factory import create_llm_provider
from jarvis.providers.tts.manager import TTSManager, format_tts_result
from jarvis.providers.tts.pipeline import SpokenResponsePipeline
from jarvis.providers.stt.manager import STTManager, format_stt_manager_result
from jarvis.providers.wake_word.manager import WakeWordManager, WakeWordMatch


class JarvisRuntime:
    """Boots the core Jarvis systems and handles user commands."""

    def __init__(self, *, project_root: str | Path | None = None, llm_provider: Any | None = None, tts_manager: TTSManager | None = None, stt_manager: STTManager | None = None) -> None:
        self.config = JarvisConfig.from_project_root(project_root)
        self.events = EventBus()
        self.logger = JarvisLogger(self.config.logs_dir)
        self.registry = AgentRegistry()
        self.ability_registry = AbilityRegistry()
        self.llm_provider = llm_provider or create_llm_provider(self.config)
        self.tts_manager = tts_manager or TTSManager(self.config, events=self.events)
        self.stt_manager = stt_manager or STTManager(self.config, events=self.events)
        self.wake_word_manager = WakeWordManager(self.config, events=self.events)
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
        configured_ltm_path = Path(str(getattr(self.config, "memory_long_term_path", "data/memory/long_term_memory.json")))
        if not configured_ltm_path.is_absolute():
            configured_ltm_path = self.config.project_root / configured_ltm_path
        self.long_term_memory = LongTermMemoryStore(
            enabled=getattr(self.config, "memory_long_term_enabled", True),
            path=configured_ltm_path,
            max_records=getattr(self.config, "memory_long_term_max_records", 0),
            inject_limit=getattr(self.config, "memory_long_term_inject_limit", 5),
        )
        configured_stf_path = Path(str(getattr(self.config, "memory_short_term_fact_path", "data/memory/short_term_memory.json")))
        if not configured_stf_path.is_absolute():
            configured_stf_path = self.config.project_root / configured_stf_path
        self.short_term_facts = ShortTermFactStore(
            enabled=getattr(self.config, "memory_short_term_fact_enabled", True),
            path=configured_stf_path,
            max_records=getattr(self.config, "memory_short_term_fact_max_records", 300),
            default_days=getattr(self.config, "memory_short_term_fact_default_days", 3),
            inject_limit=getattr(self.config, "memory_short_term_fact_inject_limit", 3),
        )
        configured_chat_dir = Path(str(getattr(self.config, "memory_chat_archive_dir", "data/memory/chat_archive")))
        if not configured_chat_dir.is_absolute():
            configured_chat_dir = self.config.project_root / configured_chat_dir
        self.chat_archive = ChatArchiveStore(
            enabled=getattr(self.config, "memory_chat_archive_enabled", True),
            root_dir=configured_chat_dir,
            max_search_days=getattr(self.config, "memory_chat_archive_max_search_days", 30),
        )
        configured_candidate_path = Path(str(getattr(self.config, "memory_candidate_path", "data/memory/memory_candidates.json")))
        if not configured_candidate_path.is_absolute():
            configured_candidate_path = self.config.project_root / configured_candidate_path
        self.memory_candidates = MemoryCandidateStore(
            enabled=getattr(self.config, "memory_candidate_enabled", True),
            path=configured_candidate_path,
            max_records=getattr(self.config, "memory_candidate_max_records", 1000),
            review_limit=getattr(self.config, "memory_candidate_review_limit", 8),
        )
        configured_entity_path = Path(str(getattr(self.config, "memory_entity_path", "data/memory/entities.json")))
        if not configured_entity_path.is_absolute():
            configured_entity_path = self.config.project_root / configured_entity_path
        self.entity_memory = EntityMemoryStore(
            enabled=getattr(self.config, "memory_entity_enabled", True),
            path=configured_entity_path,
            max_records=getattr(self.config, "memory_entity_max_records", 2000),
            inject_limit=getattr(self.config, "memory_entity_inject_limit", 5),
        )
        configured_memory_preferences_path = Path(str(getattr(self.config, "memory_preferences_path", "data/memory/memory_preferences.json")))
        if not configured_memory_preferences_path.is_absolute():
            configured_memory_preferences_path = self.config.project_root / configured_memory_preferences_path
        self.memory_preferences = MemoryPreferenceStore(
            path=configured_memory_preferences_path,
        )
        self.memory_auto_capture = MemoryAutoCaptureEngine(
            min_importance=getattr(self.config, "memory_auto_capture_min_importance", 2),
            llm_review_enabled=getattr(self.config, "memory_auto_capture_llm_review", False),
        )
        self.memory_maintenance = MemoryMaintenance(
            short_term_facts=self.short_term_facts,
            chat_archive=self.chat_archive,
            status_path=self.config.data_dir / "memory" / "maintenance_status.json",
            interval_seconds=getattr(self.config, "memory_maintenance_interval_seconds", 300),
            chat_keep_days=getattr(self.config, "memory_chat_archive_retention_days", 90),
        )
        self.started = False
        self.last_timing: TurnTimer | None = None

        self.events.subscribe("*", lambda event: self.logger.log_event(event.event_type, source=event.source, message=event.message, data=event.data))

    def boot(self) -> JarvisResult:
        self.events.emit("jarvis.boot_started", source="lifecycle", message="Jarvis boot started.")
        self.registry.load_builtin_agents()
        self.ability_registry.load_from_agent_registry(self.registry)
        self.router = JarvisRouter(
            registry=self.registry,
            events=self.events,
            llm_provider=self.llm_provider,
            config=self.config,
            short_term_memory=self.short_term_memory,
            long_term_memory=self.long_term_memory,
            short_term_fact_memory=self.short_term_facts,
            chat_archive=self.chat_archive,
            memory_candidates=self.memory_candidates,
            entity_memory=self.entity_memory,
            memory_preferences=self.memory_preferences,
            ability_registry=self.ability_registry,
        )
        self.started = True
        stt_warmup_result = None
        voice_warmup_summary = None
        if getattr(self.config, "voice_warmup_on_boot", False):
            voice_warmup_summary = self.warmup_all()
        elif getattr(self.config, "stt_warmup_on_boot", False):
            stt_warmup_result = self.stt_manager.warmup()
        agent_names = self.registry.names(enabled_only=True)
        result = JarvisResult.ok(
            f"Jarvis 3 is online. Registered {len(agent_names)} agents.",
            agent_name="lifecycle",
            action="boot",
            data={
                "agents": agent_names,
                "abilities": self.ability_registry.names(enabled_only=True),
                "ability_count": self.ability_registry.count(enabled_only=True),
                "llm_provider": getattr(self.llm_provider, "provider_name", "unknown"),
                "llm_model": getattr(self.llm_provider, "model", "unknown"),
                "llm_streaming": getattr(self.llm_provider, "streaming_enabled", False),
                "short_term_memory": self.short_term_memory.status(),
                "short_term_facts": self.short_term_facts.status(),
                "long_term_memory": self.long_term_memory.status(),
                "chat_archive": self.chat_archive.status(),
                "memory_candidates": self.memory_candidates.status(),
                "entity_memory": self.entity_memory.status(),
                "memory_preferences": self.memory_preferences.status(),
                "memory_auto_capture": {
                    "enabled": getattr(self.config, "memory_auto_capture_enabled", True),
                    "llm_review": getattr(self.config, "memory_auto_capture_llm_review", False),
                    "auto_short_term": getattr(self.config, "memory_auto_short_term_enabled", True),
                },
                "memory_maintenance": self.memory_maintenance.status(),
                "tts": {
                    "enabled": self.tts_manager.enabled,
                    "provider": self.tts_manager.provider_name,
                    "auto_speak": self.tts_manager.auto_speak,
                    "spoken_pipeline": {
                        "queue_max_size": self.spoken_pipeline.queue_max_size,
                        "chunk_max_chars": self.spoken_pipeline.chunk_max_chars,
                    },
                },
                "stt": {
                    "enabled": self.stt_manager.enabled,
                    "provider": self.stt_manager.provider_name,
                    "record_seconds": self.stt_manager.record_seconds,
                    "warmup_on_boot": getattr(self.config, "stt_warmup_on_boot", False),
                    "warmup_success": getattr(stt_warmup_result, "success", None),
                },
                "voice_warmup": {
                    "warmup_on_boot": getattr(self.config, "voice_warmup_on_boot", False),
                    "summary": voice_warmup_summary,
                },
                "voice_always_listening": {
                    "startup_enabled": getattr(self.config, "voice_always_listening_on_startup", False),
                    "startup_mode": getattr(self.config, "voice_always_listening_start_mode", "sleep_wake"),
                    "startup_max_turns": getattr(self.config, "voice_always_listening_max_turns", 0),
                },
                "wake_word": {
                    "enabled": self.wake_word_manager.enabled,
                    "provider": self.wake_word_manager.provider_name,
                    "wake_words": self.wake_word_manager.wake_words,
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
        self._record_chat_archive_turn(command, result, timing=timing)
        self._auto_capture_memory_candidate(command, result, timing=timing)
        self._run_memory_maintenance_if_due(timing=timing)
        result.data["timing"] = timing.to_dict()
        self.last_timing = timing
        self.logger.log_result(result)
        return result

    def warmup_status(self) -> str:
        """Return always-ready warmup configuration."""
        return "\n".join([
            "Always-ready warmup status:",
            f"- warmup on boot: {getattr(self.config, 'voice_warmup_on_boot', False)}",
            f"- warm STT: {getattr(self.config, 'voice_warmup_stt', True)}",
            f"- warm TTS: {getattr(self.config, 'voice_warmup_tts', True)}",
            f"- warm LLM: {getattr(self.config, 'voice_warmup_llm', False)}",
            f"- STT provider: {self.stt_manager.provider_name}",
            f"- TTS provider: {self.tts_manager.provider_name}",
            f"- always-listening on startup: {getattr(self.config, 'voice_always_listening_on_startup', False)}",
            f"- always-listening max turns: {self._format_turn_limit(getattr(self.config, 'voice_always_listening_max_turns', 0))}",
            "Commands: warmup all, stt warmup, tts warmup",
        ])

    def warmup_all(self) -> str:
        """Warm selected voice subsystems so Jarvis feels ready before use."""
        lines = ["Always-ready warmup:"]
        if getattr(self.config, "voice_warmup_stt", True):
            stt_result = self.stt_manager.warmup()
            lines.append("STT: " + stt_result.message)
        else:
            lines.append("STT: skipped")
        if getattr(self.config, "voice_warmup_tts", True):
            tts_result = self.tts_manager.warmup()
            lines.append("TTS: " + tts_result.message)
        else:
            lines.append("TTS: skipped")
        if getattr(self.config, "voice_warmup_llm", False):
            lines.append("LLM: skipped in 0.1.2; keep LM Studio warm by sending a short manual prompt after boot if needed.")
        else:
            lines.append("LLM: skipped")
        return "\n".join(lines)

    def tts_warmup(self) -> str:
        return format_tts_result(self.tts_manager.warmup())

    def audio_cleanup(self) -> str:
        tts_removed = self.tts_manager.cleanup_outputs()
        stt_removed = self.stt_manager.cleanup_recordings()
        return f"Audio cleanup complete. Removed {tts_removed} TTS file(s) and {stt_removed} STT recording file(s)."

    def tts_cleanup(self) -> str:
        return self.tts_manager.cleanup_summary()

    def stt_cleanup(self) -> str:
        return self.stt_manager.cleanup_summary()

    def stt_set_silence_seconds(self, seconds: float) -> str:
        return self.stt_manager.set_silence_seconds(seconds)

    def stt_set_energy_threshold(self, threshold: float) -> str:
        return self.stt_manager.set_energy_threshold(threshold)

    def stt_set_adaptive_energy(self, enabled: bool) -> str:
        return self.stt_manager.set_adaptive_energy(enabled)

    def stt_set_latency_preset(self, preset: str) -> str:
        return self.stt_manager.set_latency_preset(preset)

    def timing_last(self) -> str:
        """Return a readable summary for the most recent command turn."""
        return format_timing_summary(self.last_timing)


    def memory_status(self) -> str:
        """Return user-facing status for all local memory tiers."""
        return "\n\n".join([
            self.short_term_memory.format_status(),
            self.short_term_facts.format_status(),
            self.long_term_memory.format_status(),
            self.chat_archive.format_status(),
            self.memory_maintenance.format_status(),
        ])

    def memory_last(self, limit: int = 5) -> str:
        """Return recent short-term memory turns."""
        return self.short_term_memory.format_last(limit=limit)

    def memory_long_term_list(self, limit: int = 10) -> str:
        """Return recent long-term memory records."""
        return self.long_term_memory.format_records(limit=limit)

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

    def stt_status(self) -> str:
        """Return user-facing STT and microphone status."""
        return self.stt_manager.status()

    def stt_providers(self) -> str:
        """Return the configured STT provider chain."""
        return self.stt_manager.providers_summary()

    def stt_gpu_status(self) -> str:
        """Return GPU diagnostics for the active STT provider."""
        return self.stt_manager.gpu_status()

    def stt_warmup(self) -> str:
        """Warm the active STT model so the first voice turn feels faster."""
        return format_stt_manager_result(self.stt_manager.warmup())

    def stt_listen_settings(self) -> str:
        """Return low-latency microphone endpointing settings."""
        return self.stt_manager.listen_settings_summary()

    def stt_record(self) -> str:
        """Record a short microphone WAV without transcription."""
        return self.stt_manager.record_once()

    def stt_listen_once(self, *, duration_seconds: float | None = None, mode: str | None = None, silence_seconds: float | None = None) -> str:
        """Record a microphone clip with fixed or smart endpointing and transcribe it."""
        return format_stt_manager_result(self.stt_manager.listen_once(duration_seconds=duration_seconds, mode=mode, silence_seconds=silence_seconds))

    def stt_transcribe_file(self, path: str) -> str:
        """Transcribe an audio file through the STT provider chain."""
        return format_stt_manager_result(self.stt_manager.transcribe_file(path))

    def stt_debug_last(self) -> str:
        """Return detailed provider-attempt diagnostics for the last STT request."""
        return self.stt_manager.format_debug_last()

    def wake_status(self) -> str:
        """Return wake-word provider status."""
        return self.wake_word_manager.status()

    def wake_test(self, transcript: str) -> str:
        """Check typed text against the wake-word detector."""
        match = self.wake_word_manager.detect(transcript)
        return self.wake_word_manager.format_match(match)

    def wake_listen_once(
        self,
        *,
        duration_seconds: float | None = None,
        mode: str | None = None,
        silence_seconds: float | None = None,
    ) -> str:
        """Listen once, transcribe, and report whether the wake word was heard."""
        stt_result = self.stt_manager.listen_once(duration_seconds=duration_seconds, mode=mode, silence_seconds=silence_seconds)
        if not stt_result.success:
            return format_stt_manager_result(stt_result)
        match = self.wake_word_manager.detect(stt_result.text)
        lines = [format_stt_manager_result(stt_result), "", self.wake_word_manager.format_match(match)]
        return "\n".join(lines)

    def wake_voice_once(
        self,
        *,
        duration_seconds: float | None = None,
        mode: str | None = None,
        silence_seconds: float | None = None,
        stream_callback: LLMStreamCallback | None = None,
        transcript_callback: Any | None = None,
        speak: bool = True,
    ) -> JarvisResult:
        """Listen for a wake phrase and run one command if detected.

        This is a foundation step toward hands-free Jarvis. It still listens for
        one microphone turn only; a continuous wake loop will call this path in
        a later version.
        """
        if not self.started:
            self.boot()
        self.events.emit("wake_word.listen_started", source="lifecycle", message="Wake-word listen turn started.")
        stt_result = self.stt_manager.listen_once(duration_seconds=duration_seconds, mode=mode, silence_seconds=silence_seconds)
        transcript = (stt_result.text or "").strip()
        if callable(transcript_callback) and transcript:
            transcript_callback(transcript)
        if not stt_result.success:
            message = f"I could not understand the microphone input, sir. {stt_result.error or stt_result.message}"
            return JarvisResult.fail(message, agent_name="voice_agent", action="wake_voice_once", data={"stage": "stt"})
        match = self.wake_word_manager.detect(transcript)
        if not match.detected and self.wake_word_manager.require_wake_word:
            message = "Wake word was not detected, sir."
            return JarvisResult.fail(
                message,
                agent_name="voice_agent",
                action="wake_voice_once",
                data={"stage": "wake_word", "transcript": transcript, "wake_detected": False},
            )

        command = match.command.strip() if match.detected else transcript
        if not command:
            message = self.wake_word_manager.empty_response
            if speak and self.tts_manager.enabled:
                self.tts_manager.say(message, play_audio=True)
            return JarvisResult.ok(
                message,
                agent_name="voice_agent",
                action="wake_voice_once",
                data={"stage": "empty_wake", "transcript": transcript, "wake_word": match.wake_word, "wake_detected": True},
            )

        spoken_stream = None
        callback = stream_callback
        if speak and self.tts_manager.enabled:
            spoken_stream = self.spoken_pipeline.create_stream_adapter(stream_callback, enabled=True)
            callback = spoken_stream
        chat_result = self.handle_command(command, stream_callback=callback)
        spoken_chunks = self._finish_spoken_result(
            chat_result,
            spoken_stream=spoken_stream,
            wait_timeout=120.0,
            wait_message="Waiting for spoken response playback to finish.",
        )

        data = dict(chat_result.data)
        data.update(
            {
                "transcript": transcript,
                "wake_word": match.wake_word,
                "wake_detected": match.detected,
                "wake_command": command,
                "stt_provider": stt_result.provider,
                "stt_audio_path": str(stt_result.audio_path) if stt_result.audio_path else "",
                "spoken_chunks": spoken_chunks,
            }
        )
        if chat_result.success:
            return JarvisResult.ok(chat_result.message, agent_name="voice_agent", action="wake_voice_once", data=data)
        return JarvisResult.fail(chat_result.message, agent_name="voice_agent", action="wake_voice_once", errors=chat_result.errors, data=data)

    def voice_loop_status(self) -> str:
        """Return user-facing status for spoken conversation."""
        lines = [
            "Real voice loop status:",
            "- one-turn mode: listen -> transcribe -> think -> speak",
            "- continuous mode: listen repeatedly until spoken stop phrase or max turns",
            "- sleep/wake mode: sleep until wake phrase, then continue conversation until sleep phrase or inactivity",
            f"- STT enabled: {self.stt_manager.enabled}",
            f"- STT provider: {self.stt_manager.provider_name}",
            f"- listen mode: {self.stt_manager.listen_mode}",
            f"- silence stop seconds: {self.stt_manager.silence_seconds}",
            f"- TTS enabled: {self.tts_manager.enabled}",
            f"- TTS provider: {self.tts_manager.provider_name}",
            f"- playback available: {getattr(self.tts_manager, 'playback_supported', True)}",
            f"- warmup on boot: {getattr(self.config, 'voice_warmup_on_boot', False)}",
            f"- TTS retention: keep last {getattr(self.tts_manager, 'max_output_files', 30)} file(s)",
            f"- STT retention: keep last {getattr(self.stt_manager, 'max_audio_files', 30)} recording(s)",
            f"- wake word: {'enabled' if self.wake_word_manager.enabled else 'disabled'} ({', '.join(self.wake_word_manager.wake_words)})",
            f"- continuous max turns: {self._format_turn_limit(getattr(self.config, 'voice_continuous_max_turns', 25))}",
            f"- always-listening on startup: {getattr(self.config, 'voice_always_listening_on_startup', False)}",
            f"- startup always-listening max turns: {self._format_turn_limit(getattr(self.config, 'voice_always_listening_max_turns', 0))}",
            f"- continuous requires wake word: {getattr(self.config, 'voice_continuous_require_wake_word', True)}",
            f"- continuous stop phrases: {getattr(self.config, 'voice_continuous_stop_phrases', '')}",
            f"- sleep timeout: {getattr(self.config, 'voice_sleep_timeout_seconds', 45.0)}s",
            f"- sleep phrases: {getattr(self.config, 'voice_sleep_phrases', '')}",
            "Commands: voice loop once, wake voice once, handsfree start, sleep wake start, always listening start",
        ]
        return "\n".join(lines)

    def continuous_voice_loop_status(self) -> str:
        """Return focused continuous hands-free loop status."""
        lines = [
            "Continuous hands-free loop status:",
            f"- enabled foundation: True",
            f"- default requires wake word: {getattr(self.config, 'voice_continuous_require_wake_word', True)}",
            f"- max turns: {self._format_turn_limit(getattr(self.config, 'voice_continuous_max_turns', 25))}",
            f"- always-listening on startup: {getattr(self.config, 'voice_always_listening_on_startup', False)}",
            f"- startup max turns: {self._format_turn_limit(getattr(self.config, 'voice_always_listening_max_turns', 0))}",
            f"- listen mode: {self.stt_manager.listen_mode}",
            f"- silence stop seconds: {self.stt_manager.silence_seconds}",
            f"- stop phrases: {getattr(self.config, 'voice_continuous_stop_phrases', '')}",
            f"- sleep/wake timeout: {getattr(self.config, 'voice_sleep_timeout_seconds', 45.0)}s",
            f"- sleep phrases: {getattr(self.config, 'voice_sleep_phrases', '')}",
            f"- exit phrases: {getattr(self.config, 'voice_exit_phrases', '')}",
            "- interrupt/barge-in: not implemented yet",
            "Commands: handsfree start, sleep wake start, always listening start max 25 timeout 45",
        ]
        return "\n".join(lines)

    def voice_loop_once(
        self,
        *,
        duration_seconds: float | None = None,
        mode: str | None = None,
        silence_seconds: float | None = None,
        stream_callback: LLMStreamCallback | None = None,
        transcript_callback: Any | None = None,
        speak: bool = True,
    ) -> JarvisResult:
        """Run one complete spoken turn: listen, transcribe, route, stream, and speak.

        This is intentionally a one-turn loop for 0.1.0. It proves the full
        voice pipeline without keeping an always-on microphone open yet. Wake
        word and continuous conversation should build on this path later.
        """
        if not self.started:
            self.boot()

        self.events.emit("voice.loop_started", source="lifecycle", message="Voice loop turn started.")
        stt_result = self.stt_manager.listen_once(duration_seconds=duration_seconds, mode=mode, silence_seconds=silence_seconds)
        transcript = (stt_result.text or "").strip()
        if not stt_result.success:
            message = f"I could not understand the microphone input, sir. {stt_result.error or stt_result.message}"
            result = JarvisResult.fail(
                message,
                agent_name="voice_agent",
                action="voice_loop_once",
                data={"stage": "stt", "stt": stt_result.__dict__ if hasattr(stt_result, "__dict__") else str(stt_result)},
            )
            self.events.emit("voice.loop_failed", source="lifecycle", message=message, data={"stage": "stt"})
            return result

        if not transcript:
            message = "I did not catch any speech, sir."
            result = JarvisResult.fail(message, agent_name="voice_agent", action="voice_loop_once", data={"stage": "empty_transcript"})
            self.events.emit("voice.loop_failed", source="lifecycle", message=message, data={"stage": "empty_transcript"})
            return result

        if callable(transcript_callback):
            transcript_callback(transcript)
        self.events.emit("voice.loop_transcript_ready", source="lifecycle", message="Voice loop transcript ready.", data={"text": transcript})

        spoken_stream = None
        callback = stream_callback
        if speak and self.tts_manager.enabled:
            spoken_stream = self.spoken_pipeline.create_stream_adapter(stream_callback, enabled=True)
            callback = spoken_stream

        chat_result = self.handle_command(transcript, stream_callback=callback)
        spoken_chunks = self._finish_spoken_result(chat_result, spoken_stream=spoken_stream, wait_timeout=30.0)

        data = dict(chat_result.data)
        data.update(
            {
                "transcript": transcript,
                "stt_provider": stt_result.provider,
                "stt_audio_path": str(stt_result.audio_path) if stt_result.audio_path else "",
                "spoken_chunks": spoken_chunks,
                "voice_loop": True,
            }
        )
        if chat_result.success:
            result = JarvisResult.ok(chat_result.message, agent_name="voice_agent", action="voice_loop_once", data=data)
            self.events.emit("voice.loop_finished", source="lifecycle", message="Voice loop turn finished.", data={"transcript": transcript, "spoken_chunks": spoken_chunks})
            return result

        result = JarvisResult.fail(chat_result.message, agent_name="voice_agent", action="voice_loop_once", errors=chat_result.errors, data=data)
        self.events.emit("voice.loop_failed", source="lifecycle", message=chat_result.message, data={"stage": "llm"})
        return result

    def voice_loop_continuous(
        self,
        *,
        max_turns: int | None = None,
        require_wake_word: bool | None = None,
        duration_seconds: float | None = None,
        mode: str | None = None,
        silence_seconds: float | None = None,
        stream_callback: LLMStreamCallback | None = None,
        transcript_callback: Any | None = None,
        status_callback: Any | None = None,
        speak: bool = True,
    ) -> JarvisResult:
        """Run a blocking continuous spoken loop.

        This is the first hands-free loop foundation. It intentionally remains
        CLI-command controlled and blocking for 0.1.3. Use Ctrl+C or a spoken
        stop phrase such as "stop listening" to leave the loop.
        """
        if not self.started:
            self.boot()

        if max_turns is None:
            max_turns = int(getattr(self.config, "voice_continuous_max_turns", 25) or 25)
        max_turns = int(max_turns)
        infinite = max_turns <= 0
        if not infinite:
            max_turns = max(1, max_turns)
        if require_wake_word is None:
            require_wake_word = bool(getattr(self.config, "voice_continuous_require_wake_word", True))
        stop_phrases = self._voice_loop_stop_phrases()
        turns_heard = 0
        turns_handled = 0
        turns_ignored = 0
        failures = 0
        stopped_by = "max_turns"
        last_transcript = ""
        last_command = ""

        self.events.emit(
            "voice.continuous_loop_started",
            source="lifecycle",
            message="Continuous voice loop started.",
            data={"max_turns": max_turns, "require_wake_word": require_wake_word},
        )

        for turn_index in range(1, max_turns + 1):
            if callable(status_callback):
                status_callback(f"Listening turn {turn_index}/{max_turns}...")
            stt_result = self.stt_manager.listen_once(duration_seconds=duration_seconds, mode=mode, silence_seconds=silence_seconds)
            transcript = (stt_result.text or "").strip()
            last_transcript = transcript
            if transcript and callable(transcript_callback):
                transcript_callback(transcript)
            if not stt_result.success:
                failures += 1
                if callable(status_callback):
                    status_callback(f"STT failed: {stt_result.error or stt_result.message}")
                continue
            if not transcript:
                turns_ignored += 1
                if callable(status_callback):
                    status_callback("No speech detected.")
                continue
            turns_heard += 1

            if self._voice_loop_is_stop_phrase(transcript, stop_phrases):
                stopped_by = "spoken_stop_phrase"
                break

            command = transcript
            wake_detected = False
            wake_word = ""
            if require_wake_word:
                match = self.wake_word_manager.detect(transcript)
                wake_detected = match.detected
                wake_word = match.wake_word
                if not match.detected:
                    turns_ignored += 1
                    if callable(status_callback):
                        status_callback("Wake word not detected; continuing.")
                    continue
                command = (match.command or "").strip()
                if self._voice_loop_is_stop_phrase(command, stop_phrases):
                    stopped_by = "spoken_stop_phrase"
                    break
                if not command:
                    prompt = self.wake_word_manager.empty_response
                    if callable(status_callback):
                        status_callback(prompt)
                    if speak and self.tts_manager.enabled:
                        self.tts_manager.say(prompt, play_audio=True)
                    turns_handled += 1
                    last_command = ""
                    continue

            last_command = command
            if callable(status_callback) and require_wake_word:
                status_callback(f"Wake detected: {wake_word}. Command: {command}")

            spoken_stream = None
            callback = stream_callback
            if speak and self.tts_manager.enabled:
                spoken_stream = self.spoken_pipeline.create_stream_adapter(stream_callback, enabled=True)
                callback = spoken_stream
            chat_result = self.handle_command(command, stream_callback=callback)
            spoken_chunks = self._finish_spoken_result(
                chat_result,
                spoken_stream=spoken_stream,
                wait_timeout=30.0,
                wait_message="Waiting for spoken response playback to finish before the next listening turn.",
            )
            if chat_result.success:
                turns_handled += 1
                self.events.emit(
                    "voice.continuous_turn_finished",
                    source="lifecycle",
                    message="Continuous voice loop turn finished.",
                    data={"turn": turn_index, "transcript": transcript, "command": command, "wake_detected": wake_detected, "spoken_chunks": spoken_chunks},
                )
            else:
                failures += 1
                if callable(status_callback):
                    status_callback(f"Command failed: {chat_result.message}")

        if stopped_by == "max_turns" and turns_heard < max_turns:
            stopped_by = "completed"
        message = (
            f"Continuous voice loop stopped, sir. "
            f"Heard {turns_heard} turn(s), handled {turns_handled}, ignored {turns_ignored}, failures {failures}. "
            f"Stop reason: {stopped_by}."
        )
        data = {
            "turns_heard": turns_heard,
            "turns_handled": turns_handled,
            "turns_ignored": turns_ignored,
            "failures": failures,
            "stopped_by": stopped_by,
            "max_turns": max_turns,
            "require_wake_word": require_wake_word,
            "last_transcript": last_transcript,
            "last_command": last_command,
        }
        self.events.emit("voice.continuous_loop_stopped", source="lifecycle", message=message, data=data)
        return JarvisResult.ok(message, agent_name="voice_agent", action="voice_loop_continuous", data=data)

    def voice_sleep_wake_loop(
        self,
        *,
        max_turns: int | None = None,
        active_timeout_seconds: float | None = None,
        duration_seconds: float | None = None,
        mode: str | None = None,
        silence_seconds: float | None = None,
        stream_callback: LLMStreamCallback | None = None,
        transcript_callback: Any | None = None,
        status_callback: Any | None = None,
        speak: bool = True,
        stop_event: Any | None = None,
    ) -> JarvisResult:
        """Run a blocking sleep/wake hands-free loop.

        Sleep mode listens only for wake phrases. After a wake phrase is heard,
        Jarvis stays awake for normal back-and-forth conversation until a sleep
        phrase is spoken or an inactivity timeout expires. This is still a
        CLI/blocking foundation, not yet a background service.
        """
        if not self.started:
            self.boot()

        if max_turns is None:
            max_turns = int(getattr(self.config, "voice_continuous_max_turns", 25) or 25)
        max_turns = int(max_turns)
        infinite = max_turns <= 0
        if not infinite:
            max_turns = max(1, max_turns)
        if active_timeout_seconds is None:
            active_timeout_seconds = float(getattr(self.config, "voice_sleep_timeout_seconds", 45.0) or 45.0)
        active_timeout_seconds = max(1.0, float(active_timeout_seconds))

        sleep_phrases = self._voice_loop_sleep_phrases()
        exit_phrases = self._voice_loop_exit_phrases()
        state = "asleep"
        idle_seconds = 0.0
        turns_heard = 0
        turns_handled = 0
        turns_ignored = 0
        wake_activations = 0
        sleep_transitions = 0
        failures = 0
        stopped_by = "max_turns"
        last_transcript = ""
        last_command = ""

        self.events.emit(
            "voice.sleep_wake_loop_started",
            source="lifecycle",
            message="Sleep/wake voice loop started.",
            data={"max_turns": max_turns, "infinite": infinite, "active_timeout_seconds": active_timeout_seconds, "external_stop_supported": stop_event is not None},
        )

        turn_iter = itertools.count(1) if infinite else range(1, max_turns + 1)
        for turn_index in turn_iter:
            if stop_event is not None and stop_event.is_set():
                stopped_by = "external_stop"
                break
            if callable(status_callback):
                label = "sleeping" if state == "asleep" else "awake"
                limit_label = "∞" if infinite else str(max_turns)
                status_callback(f"Listening turn {turn_index}/{limit_label} ({label})...")

            stt_result = self.stt_manager.listen_once(duration_seconds=duration_seconds, mode=mode, silence_seconds=silence_seconds)
            if stop_event is not None and stop_event.is_set():
                stopped_by = "external_stop"
                break
            transcript = (stt_result.text or "").strip()
            last_transcript = transcript
            if transcript and callable(transcript_callback):
                transcript_callback(transcript)

            if not stt_result.success:
                failures += 1
                if callable(status_callback):
                    status_callback(f"STT failed: {stt_result.error or stt_result.message}")
                continue

            if not transcript:
                turns_ignored += 1
                if state == "awake":
                    idle_seconds += float(stt_result.duration_seconds or getattr(self.stt_manager, "start_timeout_seconds", 3.0) or 3.0)
                    if idle_seconds >= active_timeout_seconds:
                        state = "asleep"
                        idle_seconds = 0.0
                        sleep_transitions += 1
                        if callable(status_callback):
                            status_callback(f"No response for {active_timeout_seconds:.0f}s; returning to sleep mode.")
                elif callable(status_callback):
                    status_callback("No wake phrase heard; staying asleep.")
                continue

            turns_heard += 1
            idle_seconds = 0.0
            normalized_transcript = self._voice_loop_normalize_phrase(transcript)

            if self._voice_loop_phrase_matches(normalized_transcript, exit_phrases):
                stopped_by = "spoken_exit_phrase"
                break

            if state == "asleep":
                match = self.wake_word_manager.detect(transcript)
                if not match.detected:
                    turns_ignored += 1
                    if callable(status_callback):
                        status_callback("Wake phrase not detected; staying asleep.")
                    continue
                state = "awake"
                wake_activations += 1
                command = (match.command or "").strip()
                if callable(status_callback):
                    status_callback(f"Wake detected: {match.wake_word}. Jarvis is awake.")
                if not command:
                    prompt = self.wake_word_manager.empty_response
                    if callable(status_callback):
                        status_callback(prompt)
                    if speak and self.tts_manager.enabled:
                        self.tts_manager.say(prompt, play_audio=True)
                    continue
            else:
                if self._voice_loop_sleep_phrase_matches(normalized_transcript, sleep_phrases):
                    state = "asleep"
                    sleep_transitions += 1
                    if callable(status_callback):
                        status_callback("Sleep phrase detected; returning to sleep mode.")
                    if speak and self.tts_manager.enabled:
                        self.tts_manager.say("Going back to sleep, sir.", play_audio=True)
                    continue

                match = self.wake_word_manager.detect(transcript)
                command = (match.command or "").strip() if match.detected else transcript
                if not command:
                    command = transcript

            command_normalized = self._voice_loop_normalize_phrase(command)
            if self._voice_loop_sleep_phrase_matches(command_normalized, sleep_phrases):
                state = "asleep"
                sleep_transitions += 1
                if callable(status_callback):
                    status_callback("Sleep phrase detected; returning to sleep mode.")
                if speak and self.tts_manager.enabled:
                    self.tts_manager.say("Going back to sleep, sir.", play_audio=True)
                continue
            if self._voice_loop_phrase_matches(command_normalized, exit_phrases):
                stopped_by = "spoken_exit_phrase"
                break

            last_command = command
            spoken_stream = None
            callback = stream_callback
            if speak and self.tts_manager.enabled:
                spoken_stream = self.spoken_pipeline.create_stream_adapter(stream_callback, enabled=True)
                callback = spoken_stream
            chat_result = self.handle_command(command, stream_callback=callback)
            spoken_chunks = self._finish_spoken_result(
                chat_result,
                spoken_stream=spoken_stream,
                wait_timeout=30.0,
                wait_message="Waiting for spoken response playback to finish before the next wake/sleep turn.",
            )

            if chat_result.success:
                turns_handled += 1
                self.events.emit(
                    "voice.sleep_wake_turn_finished",
                    source="lifecycle",
                    message="Sleep/wake voice loop turn finished.",
                    data={"turn": turn_index, "transcript": transcript, "command": command, "spoken_chunks": spoken_chunks},
                )
            else:
                failures += 1
                if callable(status_callback):
                    status_callback(f"Command failed: {chat_result.message}")

        message = (
            f"Sleep/wake voice loop stopped, sir. Heard {turns_heard} turn(s), handled {turns_handled}, "
            f"ignored {turns_ignored}, wake activations {wake_activations}, sleep transitions {sleep_transitions}, "
            f"failures {failures}. Stop reason: {stopped_by}. Final state: {state}."
        )
        data = {
            "turns_heard": turns_heard,
            "turns_handled": turns_handled,
            "turns_ignored": turns_ignored,
            "wake_activations": wake_activations,
            "sleep_transitions": sleep_transitions,
            "failures": failures,
            "stopped_by": stopped_by,
            "final_state": state,
            "max_turns": max_turns,
            "infinite": infinite,
            "active_timeout_seconds": active_timeout_seconds,
            "last_transcript": last_transcript,
            "last_command": last_command,
        }
        self.events.emit("voice.sleep_wake_loop_stopped", source="lifecycle", message=message, data=data)
        return JarvisResult.ok(message, agent_name="voice_agent", action="voice_sleep_wake_loop", data=data)


    @staticmethod
    def _format_turn_limit(value: int | str | None) -> str:
        try:
            number = int(value)
        except (TypeError, ValueError):
            return str(value)
        return "infinite" if number <= 0 else str(number)

    def startup_always_listening_status(self) -> str:
        """Return startup always-listening configuration for the CLI."""
        return "\n".join([
            "Startup always-listening status:",
            f"- enabled: {getattr(self.config, 'voice_always_listening_on_startup', False)}",
            f"- mode: {getattr(self.config, 'voice_always_listening_start_mode', 'sleep_wake')}",
            f"- max turns: {self._format_turn_limit(getattr(self.config, 'voice_always_listening_max_turns', 0))}",
            f"- warmup on boot: {getattr(self.config, 'voice_warmup_on_boot', False)}",
            f"- sleep timeout: {getattr(self.config, 'voice_sleep_timeout_seconds', 45.0)}s",
            f"- wake words: {', '.join(self.wake_word_manager.wake_words)}",
            f"- sleep phrases: {getattr(self.config, 'voice_sleep_phrases', '')}",
            "Run `python scripts/run_cli.py` with startup enabled, or use `python scripts/run_jarvis_voice.py` for dedicated always-listening mode.",
        ])

    def _voice_loop_stop_phrases(self) -> list[str]:
        raw = str(getattr(self.config, "voice_continuous_stop_phrases", "") or "")
        phrases = [part.strip().lower() for part in raw.split(",") if part.strip()]
        return phrases or ["stop listening", "stop conversation", "go to sleep"]

    def _voice_loop_sleep_phrases(self) -> list[str]:
        raw = str(getattr(self.config, "voice_sleep_phrases", "") or "")
        phrases = [self._voice_loop_normalize_phrase(part) for part in raw.split(",") if part.strip()]
        return phrases or ["that s all jarvis", "thats all jarvis", "go to sleep"]

    def _voice_loop_exit_phrases(self) -> list[str]:
        raw = str(getattr(self.config, "voice_exit_phrases", "") or "")
        phrases = [self._voice_loop_normalize_phrase(part) for part in raw.split(",") if part.strip()]
        return phrases or ["exit voice mode", "stop handsfree"]

    @staticmethod
    def _voice_loop_normalize_phrase(text: str) -> str:
        return " ".join(str(text or "").lower().replace(",", " ").replace(".", " ").replace("?", " ").replace("!", " ").replace("'", " ").split())

    @classmethod
    def _voice_loop_phrase_matches(cls, text: str, phrases: list[str]) -> bool:
        normalized = cls._voice_loop_normalize_phrase(text)
        if not normalized:
            return False
        normalized_phrases = [cls._voice_loop_normalize_phrase(phrase) for phrase in phrases]
        return any(normalized == phrase or normalized.startswith(phrase + " ") for phrase in normalized_phrases if phrase)


    @classmethod
    def _voice_loop_sleep_phrase_matches(cls, text: str, phrases: list[str]) -> bool:
        """Return True when a transcript is asking Jarvis to go back to sleep.

        STT frequently mishears the assistant name in phrases like
        "that's all Jarvis" as "Dervis", "service", "Jervis", etc.
        Sleep mode should be forgiving because staying awake is more disruptive
        than requiring the exact assistant name.
        """
        normalized = cls._voice_loop_normalize_phrase(text)
        if not normalized:
            return False
        if cls._voice_loop_phrase_matches(normalized, phrases):
            return True

        tokens = normalized.split()
        if not tokens:
            return False

        assistant_aliases = {
            "jarvis",
            "jervis",
            "dervis",
            "darvis",
            "drivers",
            "travis",
            "service",
            "servis",
            "nervous",
            "jarves",
            "jarvice",
        }
        polite_tail = {"please", "sir"}

        stripped = list(tokens)
        had_assistant_tail = False
        while stripped and stripped[-1] in polite_tail:
            stripped.pop()
        while stripped and stripped[-1] in assistant_aliases:
            had_assistant_tail = True
            stripped.pop()
        while stripped and stripped[-1] in polite_tail:
            stripped.pop()

        stripped_normalized = " ".join(stripped)
        if not stripped_normalized:
            return False

        high_confidence_roots = [
            "that s all",
            "thats all",
            "that is all",
            "that will be all",
            "that ll be all",
            "that would be all",
            "that should be all",
            "that is everything",
            "thats everything",
            "go to sleep",
            "go back to sleep",
            "sleep mode",
            "standby",
            "stand by",
            "return to standby",
            "stop listening",
        ]
        if any(stripped_normalized == root or stripped_normalized.startswith(root + " ") for root in high_confidence_roots):
            return True

        assistant_required_roots = [
            "thanks",
            "thank you",
            "thanks a lot",
            "thank you very much",
            "we re done",
            "were done",
            "i m done",
            "im done",
            "all done",
            "done",
        ]
        if had_assistant_tail and any(stripped_normalized == root or stripped_normalized.startswith(root + " ") for root in assistant_required_roots):
            return True

        return False

    @staticmethod
    def _voice_loop_is_stop_phrase(text: str, stop_phrases: list[str]) -> bool:
        normalized = " ".join(str(text or "").lower().replace(",", " ").replace(".", " ").split())
        if not normalized:
            return False
        return any(normalized == phrase or normalized.startswith(phrase + " ") for phrase in stop_phrases)

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

    def _finish_spoken_result(
        self,
        result: JarvisResult,
        *,
        spoken_stream: Any | None,
        wait_timeout: float = 30.0,
        wait_message: str = "Waiting for spoken response playback to finish.",
    ) -> int:
        """Flush streamed speech and speak non-streamed agent results too.

        LLM chat can speak while text streams. Tool/agent actions usually return
        a complete message at once, so without this helper Jarvis silently shows
        the response but does not read it aloud.
        """

        spoken_chunks = 0
        if spoken_stream is not None:
            spoken_chunks = spoken_stream.finish(speak_remaining=bool(result.success and result.action == "llm_chat"))
            if result.action != "llm_chat" and result.message:
                spoken_chunks += self.spoken_pipeline.enqueue_text(result.message, source=f"{result.agent_name}.{result.action}")
            self.events.emit(
                "voice.speech_playback_wait_started",
                source="lifecycle",
                message=wait_message,
                data={"spoken_chunks": spoken_chunks, "action": result.action, "agent_name": result.agent_name},
            )
            self.spoken_pipeline.wait_until_idle(timeout=wait_timeout)
        return spoken_chunks

    def create_spoken_stream(self, display_callback=None):
        """Create a stream callback adapter for live spoken responses."""
        enabled = bool(self.tts_manager.enabled and self.tts_manager.auto_speak)
        return self.spoken_pipeline.create_stream_adapter(display_callback, enabled=enabled)

    def voice_status(self) -> str:
        """Return combined TTS, spoken output, and STT status."""
        return self.tts_manager.status() + "\n\n" + self.spoken_pipeline.status() + "\n\n" + self.stt_manager.status()

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

    def _record_chat_archive_turn(self, command: str, result: JarvisResult, *, timing: TurnTimer | None = None) -> None:
        """Archive every completed user/Jarvis turn incrementally for long uptime."""
        if not getattr(self.config, "memory_chat_archive_enabled", True):
            return
        archived = self.chat_archive.append_turn(
            user=command,
            assistant=result.message,
            session_id=self.short_term_memory.session_id,
            agent_name=result.agent_name,
            action=result.action,
            success=result.success,
            metadata={
                "intent": result.data.get("intent"),
                "selected_agent": result.data.get("selected_agent"),
                "timing_id": getattr(timing, "turn_id", ""),
            },
        )
        if archived is None:
            return
        if timing is not None:
            timing.mark("memory.chat_archive_turn_saved", archive_id=archived.id)
        self.events.emit(
            "memory.chat_archive_saved",
            source="lifecycle",
            message="Chat archive turn saved.",
            data={"archive_id": archived.id, "session_id": self.short_term_memory.session_id},
        )

    def _auto_capture_memory_candidate(self, command: str, result: JarvisResult, *, timing: TurnTimer | None = None) -> None:
        """Capture possible memories incrementally while Jarvis stays running."""
        if not getattr(self.config, "memory_auto_capture_enabled", True):
            return
        if not result.success:
            return
        # Explicit memory commands are already handled by the Memory Agent.
        if str(result.agent_name) == "memory_agent" or str(result.action).startswith("memory_"):
            return
        decision = self.memory_auto_capture.classify_turn(command, result.message, llm_provider=self.llm_provider)
        tier = str(decision.get("decision") or "ignore").lower()
        if tier in {"ignore", "chat_archive_only"}:
            return
        text = str(decision.get("text") or "").strip()
        if not text:
            return

        preference_decision = self.memory_preferences.decide(
            text,
            category=str(decision.get("category") or "general"),
            entity_hint=decision.get("entity"),
            suggested_tier=tier,
            explicit=False,
        )
        if timing is not None:
            timing.mark("memory.preference_decision", **preference_decision.to_dict())

        if preference_decision.action == "ignore":
            self.events.emit(
                "memory.auto_capture_ignored_by_preferences",
                source="lifecycle",
                message="Memory auto-capture ignored by user preferences.",
                data={"preference_decision": preference_decision.to_dict()},
            )
            return

        tags = decision.get("tags") if isinstance(decision.get("tags"), list) else []
        category = preference_decision.category or str(decision.get("category") or "general")
        importance = int(decision.get("importance") or 2)
        confidence = float(decision.get("confidence") or 0.5)

        if preference_decision.action == "save":
            long_record = self.long_term_memory.add(
                text,
                category=category,
                tags=tags,
                source="auto_capture",
                importance=importance,
                metadata={"agent_name": result.agent_name, "action": result.action, "intent": result.data.get("intent"), "entity_hint": decision.get("entity"), "memory_preference": preference_decision.to_dict()},
            )
            entity_record = None
            try:
                entity_record = self.entity_memory.upsert_from_text(
                    text,
                    source="auto_capture",
                    metadata={"source_command": command, "memory_preference": preference_decision.to_dict()},
                    confidence=confidence,
                )
            except Exception:
                entity_record = None
            if long_record is not None and timing is not None:
                timing.mark("memory.auto_long_term_saved", memory_id=long_record.id)
            self.events.emit(
                "memory.auto_long_term_saved",
                source="lifecycle",
                message="Memory saved automatically by user preference.",
                data={"memory_id": getattr(long_record, "id", ""), "entity_id": getattr(entity_record, "id", ""), "preference_decision": preference_decision.to_dict()},
            )
            return

        if preference_decision.action == "short_term" and getattr(self.config, "memory_auto_short_term_enabled", True):
            short_record = self.short_term_facts.add(
                text,
                category=category,
                tags=tags,
                source="auto_capture",
                importance=importance,
                metadata={"auto_captured": True, "memory_preference": preference_decision.to_dict()},
            )
            if short_record is not None and timing is not None:
                timing.mark("memory.auto_short_term_saved", short_term_id=short_record.id)
            return

        record = self.memory_candidates.add(
            text,
            suggested_tier=tier,
            category=category,
            tags=tags,
            importance=importance,
            confidence=confidence,
            reason=str(decision.get("reason") or preference_decision.reason or "auto-captured for review"),
            source="auto_capture",
            source_user=command,
            source_assistant=result.message,
            metadata={"agent_name": result.agent_name, "action": result.action, "intent": result.data.get("intent"), "entity_hint": decision.get("entity"), "memory_preference": preference_decision.to_dict()},
        )
        if record is not None and timing is not None:
            timing.mark("memory.candidate_saved", candidate_id=record.id, suggested_tier=record.suggested_tier)
        if record is not None:
            self.events.emit(
                "memory.candidate_saved",
                source="lifecycle",
                message="Memory candidate saved for review.",
                data={"candidate_id": record.id, "suggested_tier": record.suggested_tier, "confidence": record.confidence, "preference_decision": preference_decision.to_dict()},
            )

    def _run_memory_maintenance_if_due(self, *, timing: TurnTimer | None = None) -> None:
        """Run lightweight memory maintenance without relying on restarts."""
        status = self.memory_maintenance.run_if_due()
        if timing is not None:
            timing.mark("memory.maintenance_checked", last_run_at=status.get("last_run_at", ""))

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
            f"- temporary memory facts: {len(self.short_term_facts.records)} / {self.short_term_facts.max_records}",
            f"- chat archive: {'enabled' if getattr(self.config, 'memory_chat_archive_enabled', True) else 'disabled'}",
            f"- long-term memory: {'enabled' if getattr(self.config, 'memory_long_term_enabled', True) else 'disabled'}",
            f"- long-term memory records: {len(self.long_term_memory.records)} / {self.long_term_memory.max_records if self.long_term_memory.max_records > 0 else 'unlimited'}",
            f"- long-term injected memories: {self.long_term_memory.inject_limit}",
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
