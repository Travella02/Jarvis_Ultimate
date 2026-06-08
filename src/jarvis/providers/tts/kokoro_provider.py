"""Optional Kokoro TTS provider.

Kokoro is Jarvis's default local TTS path as of 0.0.7c. It stays
lazy so Jarvis can boot and run tests without Kokoro installed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jarvis.providers.tts.base import TTSProviderStatus, TTSRequest, TTSResult


class KokoroTTSProvider:
    provider_name = "kokoro"

    def __init__(self, *, voice_name: str = "af_heart", lang_code: str = "a") -> None:
        self.voice_name = voice_name
        self.lang_code = lang_code
        self._pipeline: Any | None = None

    def status(self) -> TTSProviderStatus:
        ok, message = self._check_imports()
        return TTSProviderStatus(
            name=self.provider_name,
            available=ok,
            ready=ok,
            message=message,
            details={"voice_name": self.voice_name, "lang_code": self.lang_code, "license_note": "Kokoro is Jarvis's default local TTS path for SaaS-ready development."},
        )

    def synthesize(self, request: TTSRequest) -> TTSResult:
        ok, message = self._check_imports()
        if not ok:
            return TTSResult.fail(message, provider=self.provider_name)
        try:
            import numpy as np
            import soundfile as sf

            pipeline = self._load_pipeline()
            requested_voice = str(request.metadata.get("kokoro_voice") or request.voice_name or "").strip()
            voice = requested_voice if requested_voice and requested_voice not in {"jarvis", "default"} else self.voice_name
            chunks = []
            for _graphemes, _phonemes, audio in pipeline(request.text, voice=voice):
                chunks.append(audio)
            if not chunks:
                return TTSResult.fail("Kokoro produced no audio chunks.", provider=self.provider_name)
            audio = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
            request.output_path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(str(request.output_path), audio, 24000)
            return TTSResult.ok(
                "Kokoro generated speech audio.",
                provider=self.provider_name,
                output_path=request.output_path,
                data={"voice_name": voice, "lang_code": self.lang_code},
            )
        except Exception as exc:
            return TTSResult.fail("Kokoro failed while generating speech.", provider=self.provider_name, error=str(exc))

    def _check_imports(self) -> tuple[bool, str]:
        try:
            import kokoro  # noqa: F401
            import soundfile  # noqa: F401
            import numpy  # noqa: F401
        except Exception as exc:
            return False, f"Kokoro optional dependencies are not installed or failed to import: {exc}"
        return True, "Kokoro optional dependencies are installed."

    def _load_pipeline(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline
        from kokoro import KPipeline

        self._pipeline = KPipeline(lang_code=self.lang_code)
        return self._pipeline
