"""Optional faster-whisper STT provider for local/offline transcription."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from jarvis.providers.stt.base import STTProviderStatus, STTRequest, STTResult


class FasterWhisperSTTProvider:
    """Lazy faster-whisper provider.

    The import and model load happen only when transcription is requested so
    Jarvis can boot without heavy STT dependencies installed.

    0.0.9b adds GPU-first support. ``device=auto`` chooses CUDA when it appears
    available and falls back to CPU if the GPU runtime is not usable.
    """

    provider_name = "faster_whisper"

    def __init__(
        self,
        *,
        model_name: str = "base.en",
        device: str = "auto",
        compute_type: str = "auto",
        vad_filter: bool = True,
        gpu_fallback_to_cpu: bool = True,
        device_index: int = 0,
    ) -> None:
        self.model_name = model_name
        self.requested_device = _normalize_requested_device(device)
        self.device = _resolve_effective_device(self.requested_device)
        self.requested_compute_type = str(compute_type or "auto").strip().lower()
        self.compute_type = _resolve_compute_type(self.requested_compute_type, self.device)
        self.vad_filter = bool(vad_filter)
        self.gpu_fallback_to_cpu = bool(gpu_fallback_to_cpu)
        self.device_index = int(device_index or 0)
        self._models: dict[tuple[str, str], Any] = {}
        self._import_error: str | None = None
        self._last_effective_device = self.device
        self._last_effective_compute_type = self.compute_type
        self._last_load_ms: float | None = None

    def status(self) -> STTProviderStatus:
        try:
            import faster_whisper  # noqa: F401
        except Exception as exc:
            self._import_error = f"{type(exc).__name__}: {exc}"
            return STTProviderStatus(
                name=self.provider_name,
                available=False,
                ready=False,
                message="faster-whisper is not installed or failed to import. Run: python -m pip install -r requirements-stt.txt",
                details={"error": self._import_error},
            )
        diagnostics = stt_gpu_diagnostics()
        message = (
            f"model={self.model_name}, requested_device={self.requested_device}, "
            f"device={self.device}, compute_type={self.compute_type}"
        )
        if self.requested_device in {"auto", "cuda"}:
            message += f", cuda_detected={diagnostics.get('cuda_detected')}"
        if self._models:
            message += ", model_loaded=True"
        return STTProviderStatus(
            name=self.provider_name,
            available=True,
            ready=True,
            message=message,
            details={
                "model": self.model_name,
                "requested_device": self.requested_device,
                "device": self.device,
                "compute_type": self.compute_type,
                "requested_compute_type": self.requested_compute_type,
                "vad_filter": self.vad_filter,
                "gpu_fallback_to_cpu": self.gpu_fallback_to_cpu,
                "device_index": self.device_index,
                "last_effective_device": self._last_effective_device,
                "last_effective_compute_type": self._last_effective_compute_type,
                "last_load_ms": self._last_load_ms,
                "gpu": diagnostics,
            },
        )

    def warmup(self) -> STTResult:
        """Load the faster-whisper model now so first live mic use is faster."""
        status = self.status()
        if not status.available:
            return STTResult.fail(status.message, provider=self.provider_name, data=status.details)
        started = time.perf_counter()
        try:
            self._load_model(self.device, self.compute_type)
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            self._last_load_ms = elapsed_ms
            return STTResult.ok(
                f"faster-whisper model warmed on {self.device} with {self.compute_type}.",
                provider=self.provider_name,
                text="",
                data={
                    "elapsed_ms": elapsed_ms,
                    "model": self.model_name,
                    "device": self.device,
                    "compute_type": self.compute_type,
                    "gpu": stt_gpu_diagnostics(),
                },
            )
        except Exception as exc:
            if self.device == "cuda" and self.gpu_fallback_to_cpu:
                try:
                    fallback_started = time.perf_counter()
                    fallback_compute_type = _resolve_compute_type("auto", "cpu")
                    self._load_model("cpu", fallback_compute_type)
                    elapsed_ms = (time.perf_counter() - fallback_started) * 1000.0
                    self._last_load_ms = elapsed_ms
                    return STTResult.ok(
                        f"CUDA warmup failed, but faster-whisper warmed on CPU fallback. CUDA error: {type(exc).__name__}: {exc}",
                        provider=self.provider_name,
                        text="",
                        data={
                            "elapsed_ms": elapsed_ms,
                            "model": self.model_name,
                            "requested_device": self.device,
                            "device": "cpu",
                            "compute_type": fallback_compute_type,
                            "cuda_error": f"{type(exc).__name__}: {exc}",
                            "gpu": stt_gpu_diagnostics(),
                        },
                    )
                except Exception as fallback_exc:
                    return STTResult.fail(
                        f"faster-whisper warmup failed on CUDA and CPU fallback: {type(fallback_exc).__name__}: {fallback_exc}",
                        provider=self.provider_name,
                        error=f"cuda={type(exc).__name__}: {exc}; cpu={type(fallback_exc).__name__}: {fallback_exc}",
                        data={"gpu": stt_gpu_diagnostics()},
                    )
            return STTResult.fail(
                f"faster-whisper warmup failed: {type(exc).__name__}: {exc}",
                provider=self.provider_name,
                error=f"{type(exc).__name__}: {exc}",
                data={"model": self.model_name, "device": self.device, "compute_type": self.compute_type, "gpu": stt_gpu_diagnostics()},
            )

    def transcribe(self, request: STTRequest) -> STTResult:
        audio_path = Path(request.audio_path)
        if not audio_path.exists():
            return STTResult.fail(f"Audio file does not exist: {audio_path}", provider=self.provider_name, audio_path=audio_path)
        status = self.status()
        if not status.available:
            return STTResult.fail(status.message, provider=self.provider_name, audio_path=audio_path, data=status.details)

        try:
            return self._transcribe_with_device(request, device=self.device, compute_type=self.compute_type, fallback_used=False)
        except Exception as exc:
            if self.device == "cuda" and self.gpu_fallback_to_cpu:
                fallback_compute_type = _resolve_compute_type("auto", "cpu")
                try:
                    result = self._transcribe_with_device(request, device="cpu", compute_type=fallback_compute_type, fallback_used=True)
                    result.message = f"CUDA STT failed; used CPU fallback. CUDA error: {type(exc).__name__}: {exc}"
                    result.data["cuda_error"] = f"{type(exc).__name__}: {exc}"
                    return result
                except Exception as fallback_exc:
                    return self._format_transcription_exception(
                        fallback_exc,
                        audio_path=audio_path,
                        extra_error=f"CUDA error before CPU fallback: {type(exc).__name__}: {exc}",
                    )
            return self._format_transcription_exception(exc, audio_path=audio_path)

    def _transcribe_with_device(self, request: STTRequest, *, device: str, compute_type: str, fallback_used: bool) -> STTResult:
        audio_path = Path(request.audio_path)
        started = time.perf_counter()
        model = self._load_model(device, compute_type)
        segments, info = model.transcribe(
            str(audio_path),
            language=request.language or None,
            initial_prompt=request.prompt or None,
            vad_filter=self.vad_filter,
            beam_size=1,
        )
        segment_data: list[dict[str, Any]] = []
        parts: list[str] = []
        for segment in segments:
            text = str(getattr(segment, "text", "") or "").strip()
            if text:
                parts.append(text)
            segment_data.append(
                {
                    "start": getattr(segment, "start", None),
                    "end": getattr(segment, "end", None),
                    "text": text,
                }
            )
        text = " ".join(parts).strip()
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        detected_language = getattr(info, "language", None) or request.language
        duration = getattr(info, "duration", None)
        self._last_effective_device = device
        self._last_effective_compute_type = compute_type
        return STTResult.ok(
            "faster-whisper transcription complete." if text else "faster-whisper completed but returned no speech text.",
            provider=self.provider_name,
            text=text,
            audio_path=audio_path,
            language=detected_language,
            duration_seconds=float(duration) if duration is not None else None,
            data={
                "elapsed_ms": elapsed_ms,
                "model": self.model_name,
                "requested_device": self.requested_device,
                "device": device,
                "compute_type": compute_type,
                "fallback_used": fallback_used,
                "vad_filter": self.vad_filter,
                "segments": segment_data,
            },
        )

    def _format_transcription_exception(self, exc: Exception, *, audio_path: Path, extra_error: str | None = None) -> STTResult:
        message = f"faster-whisper failed while transcribing audio: {type(exc).__name__}: {exc}"
        if extra_error:
            message = f"{message}. {extra_error}"
        return STTResult.fail(
            message,
            provider=self.provider_name,
            audio_path=audio_path,
            error=f"{type(exc).__name__}: {exc}",
            data={
                "model": self.model_name,
                "requested_device": self.requested_device,
                "device": self.device,
                "compute_type": self.compute_type,
                "gpu": stt_gpu_diagnostics(),
                "extra_error": extra_error or "",
            },
        )

    def _load_model(self, device: str, compute_type: str) -> Any:
        key = (device, compute_type)
        if key in self._models:
            return self._models[key]
        from faster_whisper import WhisperModel

        started = time.perf_counter()
        kwargs: dict[str, Any] = {"device": device, "compute_type": compute_type}
        if device == "cuda":
            kwargs["device_index"] = self.device_index
        model = WhisperModel(self.model_name, **kwargs)
        self._models[key] = model
        self._last_load_ms = (time.perf_counter() - started) * 1000.0
        self._last_effective_device = device
        self._last_effective_compute_type = compute_type
        return model


def _normalize_requested_device(value: str | None) -> str:
    text = str(value or "auto").strip().lower()
    if text in {"cuda", "gpu", "nvidia"}:
        return "cuda"
    if text in {"cpu"}:
        return "cpu"
    return "auto"


def _resolve_effective_device(requested: str) -> str:
    if requested == "cuda":
        return "cuda"
    if requested == "cpu":
        return "cpu"
    return "cuda" if stt_gpu_diagnostics().get("cuda_detected") else "cpu"


def _resolve_compute_type(value: str | None, device: str) -> str:
    text = str(value or "auto").strip().lower()
    if text in {"", "auto", "default"}:
        return "float16" if device == "cuda" else "int8"
    if text in {"fp16"}:
        return "float16"
    if text in {"int8-float16", "int8_float16"}:
        return "int8_float16"
    if text in {"float16", "float32", "int8"}:
        return text
    return "float16" if device == "cuda" else "int8"


def stt_gpu_diagnostics() -> dict[str, Any]:
    """Return lightweight CUDA diagnostics without loading a Whisper model."""
    diagnostics: dict[str, Any] = {
        "cuda_detected": False,
        "ctranslate2_cuda_devices": None,
        "torch_cuda_available": None,
        "torch_gpu_name": "",
        "notes": [],
    }
    try:
        import ctranslate2

        if hasattr(ctranslate2, "get_cuda_device_count"):
            count = int(ctranslate2.get_cuda_device_count())
            diagnostics["ctranslate2_cuda_devices"] = count
            if count > 0:
                diagnostics["cuda_detected"] = True
        else:
            diagnostics["notes"].append("ctranslate2 has no get_cuda_device_count helper")
    except Exception as exc:
        diagnostics["notes"].append(f"ctranslate2 CUDA check failed: {type(exc).__name__}: {exc}")
    try:
        import torch

        available = bool(torch.cuda.is_available())
        diagnostics["torch_cuda_available"] = available
        if available:
            diagnostics["cuda_detected"] = True
            diagnostics["torch_gpu_name"] = torch.cuda.get_device_name(0)
    except Exception as exc:
        diagnostics["notes"].append(f"torch CUDA check failed: {type(exc).__name__}: {exc}")
    return diagnostics
