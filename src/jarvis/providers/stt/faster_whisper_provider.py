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
    """

    provider_name = "faster_whisper"

    def __init__(
        self,
        *,
        model_name: str = "base.en",
        device: str = "cpu",
        compute_type: str = "int8",
        vad_filter: bool = True,
    ) -> None:
        self.model_name = model_name
        self.device = _normalize_device(device)
        self.compute_type = compute_type or _default_compute_type(self.device)
        self.vad_filter = bool(vad_filter)
        self._model: Any | None = None
        self._import_error: str | None = None

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
        return STTProviderStatus(
            name=self.provider_name,
            available=True,
            ready=True,
            message=f"model={self.model_name}, device={self.device}, compute_type={self.compute_type}",
            details={"model": self.model_name, "device": self.device, "compute_type": self.compute_type, "vad_filter": self.vad_filter},
        )

    def transcribe(self, request: STTRequest) -> STTResult:
        audio_path = Path(request.audio_path)
        if not audio_path.exists():
            return STTResult.fail(f"Audio file does not exist: {audio_path}", provider=self.provider_name, audio_path=audio_path)
        status = self.status()
        if not status.available:
            return STTResult.fail(status.message, provider=self.provider_name, audio_path=audio_path, data=status.details)

        started = time.perf_counter()
        try:
            model = self._load_model()
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
                    "device": self.device,
                    "compute_type": self.compute_type,
                    "vad_filter": self.vad_filter,
                    "segments": segment_data,
                },
            )
        except Exception as exc:
            return STTResult.fail(
                f"faster-whisper failed while transcribing audio: {type(exc).__name__}: {exc}",
                provider=self.provider_name,
                audio_path=audio_path,
                error=f"{type(exc).__name__}: {exc}",
                data={"model": self.model_name, "device": self.device, "compute_type": self.compute_type},
            )

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        from faster_whisper import WhisperModel

        self._model = WhisperModel(self.model_name, device=self.device, compute_type=self.compute_type)
        return self._model


def _normalize_device(value: str | None) -> str:
    text = str(value or "cpu").strip().lower()
    if text in {"cuda", "gpu"}:
        return "cuda"
    if text in {"auto"}:
        # Keep default conservative for first STT foundation. GPU can be enabled
        # explicitly with JARVIS_STT_DEVICE=cuda once dependencies are verified.
        return "cpu"
    return "cpu"


def _default_compute_type(device: str) -> str:
    return "float16" if device == "cuda" else "int8"
