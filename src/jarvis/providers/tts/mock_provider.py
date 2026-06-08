"""Safe mock TTS provider used by tests and as a final fallback."""

from __future__ import annotations

from jarvis.providers.tts.base import TTSProviderStatus, TTSRequest, TTSResult


class MockTTSProvider:
    """A dependency-free provider that writes a small text placeholder.

    This lets Jarvis test TTS routing without installing GPU TTS packages.
    """

    provider_name = "mock"

    def status(self) -> TTSProviderStatus:
        return TTSProviderStatus(
            name=self.provider_name,
            available=True,
            ready=True,
            message="dependency-free placeholder provider",
        )

    def synthesize(self, request: TTSRequest) -> TTSResult:
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        placeholder_path = request.output_path.with_suffix(".txt")
        placeholder_path.write_text(request.text, encoding="utf-8")
        return TTSResult.ok(
            "Mock TTS captured the text. No real audio was generated.",
            provider=self.provider_name,
            output_path=placeholder_path,
            data={"chars": len(request.text), "voice_name": request.voice_name},
        )
