"""STT manager for microphone recording, transcription, and diagnostics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.core.events import EventBus
from jarvis.providers.stt.audio_recorder import MicrophoneRecorder, format_record_result
from jarvis.providers.stt.base import STTProvider, STTRequest, STTResult, format_stt_result
from jarvis.providers.stt.factory import create_stt_provider, normalize_provider_name, parse_fallback_chain


class STTManager:
    """Coordinates swappable STT providers without coupling them to the brain."""

    def __init__(self, config: Any, *, events: EventBus | None = None, recorder: MicrophoneRecorder | None = None) -> None:
        self.config = config
        self.events = events or EventBus()
        self.enabled = bool(getattr(config, "stt_enabled", True))
        self.provider_name = normalize_provider_name(getattr(config, "stt_provider", "faster_whisper"))
        fallback_value = getattr(config, "stt_fallback_providers", "mock")
        self.fallback_providers = [name for name in parse_fallback_chain(fallback_value) if name != self.provider_name]
        if "mock" not in self.fallback_providers:
            self.fallback_providers.append("mock")
        self.project_root = Path(getattr(config, "project_root", Path.cwd()))
        self.output_dir = self._resolve_project_path(getattr(config, "stt_output_dir", "data/stt"))
        self.language = str(getattr(config, "stt_language", "en") or "").strip() or None
        self.record_seconds = float(getattr(config, "stt_record_seconds", 4.0))
        self.sample_rate = int(getattr(config, "stt_sample_rate", 16000))
        self.channels = int(getattr(config, "stt_channels", 1))
        self.microphone_device = str(getattr(config, "stt_microphone_device", "") or "").strip() or None
        self._providers: dict[str, STTProvider] = {}
        self.recorder = recorder or MicrophoneRecorder(
            output_dir=self.output_dir,
            sample_rate=self.sample_rate,
            channels=self.channels,
            device=self.microphone_device,
        )
        self.last_result: STTResult | None = None
        self.last_attempts: list[dict[str, Any]] = []
        self.last_recording: Any | None = None

    def status(self) -> str:
        lines = [
            "STT/microphone status:",
            f"- enabled: {self.enabled}",
            f"- preferred provider: {self.provider_name}",
            f"- fallback providers: {', '.join(self.fallback_providers) if self.fallback_providers else 'none'}",
            f"- model: {getattr(self.config, 'stt_model', 'base.en')}",
            f"- language: {self.language or 'auto'}",
            f"- device: {getattr(self.config, 'stt_device', 'cpu')}",
            f"- compute type: {getattr(self.config, 'stt_compute_type', 'int8')}",
            f"- record seconds: {self.record_seconds}",
            f"- sample rate: {self.sample_rate}",
            f"- channels: {self.channels}",
            f"- output dir: {self.output_dir}",
        ]
        mic = self.recorder.status()
        lines.append(f"- microphone: {'ready' if mic.get('ready') else 'unavailable'} - {mic.get('message', '')}")
        lines.append("Provider checks:")
        for provider_name in self.provider_chain():
            lines.append(f"- {self.get_provider(provider_name).status().format_line()}")
        return "\n".join(lines)

    def providers_summary(self) -> str:
        lines = ["Available STT provider chain:"]
        for index, provider_name in enumerate(self.provider_chain(), start=1):
            marker = "preferred" if index == 1 else "fallback"
            lines.append(f"{index}. {provider_name} ({marker}) - {self.get_provider(provider_name).status().format_line()}")
        lines.append("Use 'listen once' to record and transcribe a short microphone clip. Use 'stt transcribe <path>' to test an audio file.")
        return "\n".join(lines)

    def record_once(self, *, duration_seconds: float | None = None) -> str:
        result = self.recorder.record(duration_seconds=duration_seconds or self.record_seconds)
        self.last_recording = result
        return format_record_result(result)

    def listen_once(self, *, duration_seconds: float | None = None) -> STTResult:
        if not self.enabled:
            result = STTResult.fail("STT is disabled. Set JARVIS_STT_ENABLED=true to enable microphone input.", provider="stt_manager")
            self.last_result = result
            return result
        record_result = self.recorder.record(duration_seconds=duration_seconds or self.record_seconds)
        self.last_recording = record_result
        if not record_result.success or record_result.output_path is None:
            result = STTResult.fail(
                "Could not record microphone audio for STT.",
                provider="stt_manager",
                error=record_result.error or record_result.message,
                data={"recording": record_result.data},
            )
            self.last_result = result
            return result
        return self.transcribe_file(record_result.output_path)

    def transcribe_file(self, path: str | Path) -> STTResult:
        if not self.enabled:
            result = STTResult.fail("STT is disabled. Set JARVIS_STT_ENABLED=true to enable speech input.", provider="stt_manager")
            self.last_result = result
            return result
        audio_path = self._resolve_project_path(path)
        request = STTRequest(audio_path=audio_path, language=self.language)
        selected_chain = self.provider_chain()
        errors: list[str] = []
        attempts: list[dict[str, Any]] = []
        self.last_attempts = []
        self.events.emit("voice.stt_requested", source="stt.manager", message="STT requested.", data={"audio_path": str(audio_path), "provider_chain": selected_chain})
        for provider_name in selected_chain:
            provider = self.get_provider(provider_name)
            status = provider.status()
            attempt: dict[str, Any] = {"provider": provider_name, "available": status.available, "ready": status.ready, "status_message": status.message}
            if not status.available:
                errors.append(f"{provider_name}: {status.message}")
                attempt.update({"success": False, "error": status.message, "details": status.details})
                attempts.append(attempt)
                continue
            result = provider.transcribe(request)
            attempt.update({"success": result.success, "message": result.message, "error": result.error or "", "text": result.text, "data": result.data})
            attempts.append(attempt)
            if result.success:
                result.data.setdefault("attempts", attempts)
                result.data.setdefault("provider_chain", selected_chain)
                self.last_result = result
                self.last_attempts = attempts
                self.events.emit("voice.stt_finished", source="stt.manager", message=result.message, data={"provider": result.provider, "text_chars": len(result.text), "audio_path": str(audio_path)})
                return result
            errors.append(f"{provider_name}: {result.error or result.message}")
        message = "No STT provider could transcribe audio. " + " | ".join(errors)
        failed = STTResult.fail(message, provider="stt_manager", audio_path=audio_path, data={"errors": errors, "attempts": attempts, "provider_chain": selected_chain})
        self.last_result = failed
        self.last_attempts = attempts
        self.events.emit("voice.stt_failed", source="stt.manager", message=message, data={"errors": errors, "attempts": attempts})
        return failed

    def format_debug_last(self) -> str:
        if self.last_result is None and not self.last_attempts:
            return "No STT debug information is available yet. Run 'listen once' or 'stt transcribe <path>' first."
        lines = ["Last STT debug:"]
        if self.last_result is not None:
            lines.extend([
                f"- final success: {self.last_result.success}",
                f"- final provider: {self.last_result.provider}",
                f"- final message: {self.last_result.message}",
            ])
            if self.last_result.error:
                lines.append(f"- final error: {self.last_result.error}")
            if self.last_result.text:
                lines.append(f"- final text: {self.last_result.text}")
        if self.last_recording is not None:
            lines.append("Recording:")
            lines.extend("  " + line for line in format_record_result(self.last_recording).splitlines())
        if self.last_attempts:
            lines.append("Provider attempts:")
            for index, attempt in enumerate(self.last_attempts, start=1):
                lines.append(f"{index}. {attempt.get('provider')} success={attempt.get('success')} ready={attempt.get('ready')} available={attempt.get('available')}")
                if attempt.get("status_message"):
                    lines.append(f"   status: {attempt['status_message']}")
                if attempt.get("text"):
                    lines.append(f"   text: {attempt['text']}")
                if attempt.get("error"):
                    lines.append(f"   error: {attempt['error']}")
        return "\n".join(lines)

    def provider_chain(self) -> list[str]:
        chain = [self.provider_name]
        chain.extend(name for name in self.fallback_providers if name not in chain)
        return chain

    def get_provider(self, provider_name: str) -> STTProvider:
        normalized = normalize_provider_name(provider_name)
        if normalized not in self._providers:
            self._providers[normalized] = create_stt_provider(normalized, self.config)
        return self._providers[normalized]

    def _resolve_project_path(self, value: str | Path) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return self.project_root / path


def format_stt_manager_result(result: STTResult) -> str:
    return format_stt_result(result)
