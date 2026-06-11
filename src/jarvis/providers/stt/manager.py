"""STT manager for microphone recording, transcription, and diagnostics."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.core.events import EventBus
from jarvis.providers.stt.audio_recorder import MicrophoneRecorder, format_record_result
from jarvis.providers.stt.base import STTProvider, STTRequest, STTResult, format_stt_result
from jarvis.providers.stt.factory import create_stt_provider, normalize_provider_name, parse_fallback_chain
from jarvis.providers.stt.faster_whisper_provider import stt_gpu_diagnostics


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
        self.max_audio_files = int(getattr(config, "stt_max_audio_files", 30))
        self.last_cleanup_removed = 0
        self.language = str(getattr(config, "stt_language", "en") or "").strip() or None
        self.record_seconds = float(getattr(config, "stt_record_seconds", 2.0))
        self.listen_mode = _normalize_listen_mode(getattr(config, "stt_listen_mode", "smart"))
        self.max_listen_seconds = float(getattr(config, "stt_max_listen_seconds", 8.0))
        self.silence_seconds = float(getattr(config, "stt_silence_seconds", 1.0))
        self.min_record_seconds = float(getattr(config, "stt_min_record_seconds", 0.35))
        self.start_timeout_seconds = float(getattr(config, "stt_start_timeout_seconds", 5.0))
        self.energy_threshold = float(getattr(config, "stt_energy_threshold", 0.018))
        self.adaptive_energy = bool(getattr(config, "stt_adaptive_energy", True))
        self.ambient_calibration_seconds = float(getattr(config, "stt_ambient_calibration_seconds", 0.35))
        self.energy_multiplier = float(getattr(config, "stt_energy_multiplier", 3.0))
        self.pre_roll_seconds = float(getattr(config, "stt_pre_roll_seconds", 0.25))
        self.frame_ms = int(getattr(config, "stt_frame_ms", 30))
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
            f"- requested device: {getattr(self.config, 'stt_device', 'auto')}",
            f"- compute type: {getattr(self.config, 'stt_compute_type', 'auto')}",
            f"- GPU fallback to CPU: {getattr(self.config, 'stt_gpu_fallback_to_cpu', True)}",
            f"- warmup on boot: {getattr(self.config, 'stt_warmup_on_boot', False)}",
            f"- fixed record seconds: {self.record_seconds}",
            f"- listen mode: {self.listen_mode}",
            f"- max listen seconds: {self.max_listen_seconds}",
            f"- silence stop seconds: {self.silence_seconds}",
            f"- start timeout seconds: {self.start_timeout_seconds}",
            f"- energy threshold: {self.energy_threshold}",
            f"- adaptive energy: {self.adaptive_energy}",
            f"- ambient calibration seconds: {self.ambient_calibration_seconds}",
            f"- energy multiplier: {self.energy_multiplier}",
            f"- sample rate: {self.sample_rate}",
            f"- channels: {self.channels}",
            f"- output dir: {self.output_dir}",
            f"- retention: keep last {self.max_audio_files} microphone WAV file(s)",
        ]
        mic = self.recorder.status()
        lines.append(f"- microphone: {'ready' if mic.get('ready') else 'unavailable'} - {mic.get('message', '')}")
        gpu = stt_gpu_diagnostics()
        lines.append(f"- CUDA detected for STT: {gpu.get('cuda_detected')}")
        if gpu.get("torch_gpu_name"):
            lines.append(f"- torch GPU: {gpu.get('torch_gpu_name')}")
        if gpu.get("ctranslate2_cuda_devices") is not None:
            lines.append(f"- CTranslate2 CUDA devices: {gpu.get('ctranslate2_cuda_devices')}")
        if gpu.get("notes"):
            lines.append("- GPU notes: " + " | ".join(str(item) for item in gpu.get("notes", [])))
        lines.append("Provider checks:")
        for provider_name in self.provider_chain():
            lines.append(f"- {self.get_provider(provider_name).status().format_line()}")
        return "\n".join(lines)

    def providers_summary(self) -> str:
        lines = ["Available STT provider chain:"]
        for index, provider_name in enumerate(self.provider_chain(), start=1):
            marker = "preferred" if index == 1 else "fallback"
            lines.append(f"{index}. {provider_name} ({marker}) - {self.get_provider(provider_name).status().format_line()}")
        lines.append("Use 'stt warmup' before live voice tests so the first transcription is not delayed by model loading.")
        lines.append("Use 'listen once' for smart silence-based endpointing, 'listen fixed 2' for a fixed timer, or 'stt transcribe <path>' to test an audio file.")
        return "\n".join(lines)

    def gpu_status(self) -> str:
        gpu = stt_gpu_diagnostics()
        lines = ["STT GPU diagnostics:"]
        lines.append(f"- requested device: {getattr(self.config, 'stt_device', 'auto')}")
        lines.append(f"- compute type: {getattr(self.config, 'stt_compute_type', 'auto')}")
        lines.append(f"- CUDA detected: {gpu.get('cuda_detected')}")
        lines.append(f"- torch cuda available: {gpu.get('torch_cuda_available')}")
        if gpu.get("torch_gpu_name"):
            lines.append(f"- torch GPU: {gpu.get('torch_gpu_name')}")
        lines.append(f"- CTranslate2 CUDA devices: {gpu.get('ctranslate2_cuda_devices')}")
        notes = gpu.get("notes") or []
        if notes:
            lines.append("Notes:")
            lines.extend(f"- {note}" for note in notes)
        lines.append("If CUDA is detected but model load fails, run 'stt debug last'. On Windows, CTranslate2 may still need NVIDIA cuBLAS/cuDNN DLLs in PATH.")
        return "\n".join(lines)

    def warmup(self) -> STTResult:
        if not self.enabled:
            result = STTResult.fail("STT is disabled. Set JARVIS_STT_ENABLED=true to enable microphone input.", provider="stt_manager")
            self.last_result = result
            return result
        provider = self.get_provider(self.provider_name)
        if not hasattr(provider, "warmup"):
            result = STTResult.fail(f"Provider '{self.provider_name}' does not support warmup.", provider=self.provider_name)
            self.last_result = result
            return result
        result = provider.warmup()  # type: ignore[attr-defined]
        self.last_result = result
        self.last_attempts = [
            {
                "provider": self.provider_name,
                "success": result.success,
                "ready": result.success,
                "available": True,
                "message": result.message,
                "error": result.error or "",
                "data": result.data,
            }
        ]
        return result

    def record_once(self, *, duration_seconds: float | None = None) -> str:
        result = self.recorder.record(duration_seconds=duration_seconds or self.record_seconds)
        self.last_recording = result
        if result.success:
            self.cleanup_recordings()
        return format_record_result(result)

    def listen_settings_summary(self) -> str:
        """Return the current low-latency listen settings."""
        return "\n".join([
            "STT listen/endpointing settings:",
            f"- listen mode: {self.listen_mode}",
            f"- fixed record seconds: {self.record_seconds}",
            f"- max listen seconds: {self.max_listen_seconds}",
            f"- silence stop seconds: {self.silence_seconds}",
            f"- min record seconds: {self.min_record_seconds}",
            f"- start timeout seconds: {self.start_timeout_seconds}",
            f"- energy threshold: {self.energy_threshold}",
            f"- adaptive energy: {self.adaptive_energy}",
            f"- ambient calibration seconds: {self.ambient_calibration_seconds}",
            f"- energy multiplier: {self.energy_multiplier}",
            f"- pre-roll seconds: {self.pre_roll_seconds}",
            f"- frame ms: {self.frame_ms}",
            "Presets: listen faster = 0.55s, listen balanced = 0.75s, listen safer = 1.05s",
            "Tuning: use 'stt energy 0.03' if Jarvis keeps listening until max duration, or 'stt energy 0.015' if Jarvis misses quiet speech.",
        ])

    def listen_once(self, *, duration_seconds: float | None = None, mode: str | None = None, silence_seconds: float | None = None) -> STTResult:
        if not self.enabled:
            result = STTResult.fail("STT is disabled. Set JARVIS_STT_ENABLED=true to enable microphone input.", provider="stt_manager")
            self.last_result = result
            return result
        listen_mode = _normalize_listen_mode(mode or self.listen_mode)
        if listen_mode == "smart":
            record_result = self.recorder.record_until_silence(
                max_duration_seconds=duration_seconds or self.max_listen_seconds,
                silence_seconds=silence_seconds or self.silence_seconds,
                min_record_seconds=self.min_record_seconds,
                start_timeout_seconds=self.start_timeout_seconds,
                energy_threshold=self.energy_threshold,
                pre_roll_seconds=self.pre_roll_seconds,
                frame_ms=self.frame_ms,
                adaptive_energy=self.adaptive_energy,
                ambient_calibration_seconds=self.ambient_calibration_seconds,
                energy_multiplier=self.energy_multiplier,
            )
        else:
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
        result = self.transcribe_file(record_result.output_path)
        self.cleanup_recordings()
        return result

    def set_silence_seconds(self, seconds: float) -> str:
        value = float(seconds)
        if value < 0.35:
            value = 0.35
        if value > 2.5:
            value = 2.5
        self.silence_seconds = value
        setattr(self.config, "stt_silence_seconds", value)
        return f"Smart listen silence stop is now {value:.2f}s for this runtime session."

    def set_latency_preset(self, preset: str) -> str:
        selected = str(preset or "balanced").strip().lower()
        presets = {"faster": 0.55, "fast": 0.55, "balanced": 0.75, "normal": 0.75, "safer": 1.05, "safe": 1.05}
        if selected not in presets:
            return "Unknown listen preset. Use: listen faster, listen balanced, or listen safer."
        return self.set_silence_seconds(presets[selected])


    def set_energy_threshold(self, threshold: float) -> str:
        value = float(threshold)
        if value < 0.003:
            value = 0.003
        if value > 0.2:
            value = 0.2
        self.energy_threshold = value
        setattr(self.config, "stt_energy_threshold", value)
        return f"Smart listen base energy threshold is now {value:.4f} for this runtime session."

    def set_adaptive_energy(self, enabled: bool) -> str:
        self.adaptive_energy = bool(enabled)
        setattr(self.config, "stt_adaptive_energy", self.adaptive_energy)
        state = "on" if self.adaptive_energy else "off"
        return f"Smart listen adaptive energy is now {state} for this runtime session."

    def cleanup_recordings(self) -> int:
        removed = _cleanup_old_files(self.output_dir, pattern="jarvis_mic_*.wav", keep_last=self.max_audio_files)
        self.last_cleanup_removed = removed
        if removed:
            self.events.emit("voice.stt_cleanup_finished", source="stt.manager", message="Old microphone recordings cleaned up.", data={"removed": removed, "keep_last": self.max_audio_files})
        return removed

    def cleanup_summary(self) -> str:
        removed = self.cleanup_recordings()
        return f"STT cleanup complete. Removed {removed} old microphone recording file(s). Keeping last {self.max_audio_files}."

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
                data = attempt.get("data") or {}
                if attempt.get("text"):
                    lines.append(f"   text: {attempt['text']}")
                if data.get("device"):
                    lines.append(f"   device: {data.get('device')} ({data.get('compute_type', 'unknown compute type')})")
                if data.get("elapsed_ms") is not None:
                    lines.append(f"   elapsed_ms: {float(data.get('elapsed_ms')):.1f}")
                if data.get("fallback_used"):
                    lines.append("   fallback_used: True")
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


def _cleanup_old_files(directory: Path, *, pattern: str, keep_last: int) -> int:
    try:
        keep = int(keep_last)
    except Exception:
        keep = 30
    if keep < 0 or not directory.exists():
        return 0
    files = [path for path in directory.glob(pattern) if path.is_file()]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    to_remove = files[keep:] if keep > 0 else files
    removed = 0
    for path in to_remove:
        try:
            path.unlink()
            removed += 1
        except OSError:
            pass
    return removed


def format_stt_manager_result(result: STTResult) -> str:
    return format_stt_result(result)


def _normalize_listen_mode(value: object) -> str:
    text = str(value or "smart").strip().lower().replace("-", "_")
    if text in {"fixed", "timer", "duration", "manual"}:
        return "fixed"
    return "smart"
