"""Optional XTTS v2 provider for personal local Jarvis voice experiments.

XTTS v2 is intentionally loaded lazily because it is a heavy optional GPU model.
It is useful for a personal Jarvis voice, but its public model license is
non-commercial, so SaaS/commercial builds should swap this provider out.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.providers.tts.base import TTSProviderStatus, TTSRequest, TTSResult


class XTTSTTSProvider:
    provider_name = "xtts"

    def __init__(
        self,
        *,
        model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2",
        use_gpu: bool = True,
        device: str = "cuda",
        speaker_wav: str | Path | None = None,
    ) -> None:
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.device = device
        self.speaker_wav = Path(speaker_wav).expanduser() if speaker_wav else None
        self._engine: Any | None = None
        self._load_error: str | None = None

    def status(self) -> TTSProviderStatus:
        import_check = self._check_imports()
        ready = import_check[0] and self._speaker_is_usable()
        details = {
            "model_name": self.model_name,
            "use_gpu": self.use_gpu,
            "device": self.device,
            "speaker_wav": str(self.speaker_wav) if self.speaker_wav else "",
            "license_note": "XTTS v2 public model license is non-commercial; swap for SaaS/commercial use.",
        }
        if not import_check[0]:
            return TTSProviderStatus(name=self.provider_name, available=False, ready=False, message=import_check[1], details=details)
        if not self._speaker_is_usable():
            return TTSProviderStatus(
                name=self.provider_name,
                available=True,
                ready=False,
                message="XTTS package found, but no usable speaker reference WAV is configured yet.",
                details=details,
            )
        return TTSProviderStatus(name=self.provider_name, available=True, ready=True, message="XTTS is configured for local synthesis.", details=details)

    def synthesize(self, request: TTSRequest) -> TTSResult:
        import_ok, import_message = self._check_imports()
        if not import_ok:
            return TTSResult.fail(import_message, provider=self.provider_name)

        speaker_wav = request.speaker_wav or self.speaker_wav
        if speaker_wav is None or not Path(speaker_wav).exists():
            return TTSResult.fail(
                "XTTS needs a clean speaker reference WAV. Set JARVIS_TTS_XTTS_SPEAKER_WAV or place one at assets/voices/jarvis_reference.wav.",
                provider=self.provider_name,
                data={"speaker_wav": str(speaker_wav) if speaker_wav else ""},
            )

        try:
            engine = self._load_engine()
            request.output_path.parent.mkdir(parents=True, exist_ok=True)
            engine.tts_to_file(
                text=request.text,
                file_path=str(request.output_path),
                speaker_wav=str(speaker_wav),
                language=request.language or "en",
            )
            return TTSResult.ok(
                "XTTS generated speech audio.",
                provider=self.provider_name,
                output_path=request.output_path,
                data={"model_name": self.model_name, "speaker_wav": str(speaker_wav), "language": request.language or "en"},
            )
        except Exception as exc:  # Keep Jarvis safe if the optional engine fails.
            return TTSResult.fail("XTTS failed while generating speech.", provider=self.provider_name, error=str(exc))

    def _check_imports(self) -> tuple[bool, str]:
        try:
            import TTS.api  # noqa: F401
        except Exception as exc:
            return False, f"XTTS optional dependency is not installed or failed to import: {exc}"
        return True, "XTTS optional dependency is installed."

    def _speaker_is_usable(self) -> bool:
        return self.speaker_wav is not None and self.speaker_wav.exists()

    def _load_engine(self) -> Any:
        if self._engine is not None:
            return self._engine
        from TTS.api import TTS

        try:
            self._engine = TTS(self.model_name, gpu=self.use_gpu)
        except TypeError:
            # Newer Coqui/TTS versions may not accept gpu=. Load first, then move
            # to the requested device if the object exposes .to().
            self._engine = TTS(self.model_name)
            if self.use_gpu and hasattr(self._engine, "to"):
                self._engine.to(self.device)
        return self._engine
