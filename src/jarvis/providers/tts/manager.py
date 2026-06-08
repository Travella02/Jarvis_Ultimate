"""TTS manager for provider selection, fallback, and optional playback."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.core.events import EventBus
from jarvis.providers.tts.base import TTSProvider, TTSRequest, TTSResult
from jarvis.providers.tts.factory import create_tts_provider, normalize_provider_name, parse_fallback_chain


class TTSManager:
    """Coordinates swappable TTS providers without coupling them to the brain."""

    def __init__(self, config: Any, *, events: EventBus | None = None) -> None:
        self.config = config
        self.events = events or EventBus()
        self.enabled = bool(getattr(config, "tts_enabled", True))
        self.auto_speak = bool(getattr(config, "tts_auto_speak", False))
        self.provider_name = normalize_provider_name(getattr(config, "tts_provider", "xtts"))
        fallback_value = getattr(config, "tts_fallback_providers", "kokoro,mock")
        self.fallback_providers = [name for name in parse_fallback_chain(fallback_value) if name != self.provider_name]
        if "mock" not in self.fallback_providers:
            self.fallback_providers.append("mock")
        self.output_dir = self._resolve_output_dir(getattr(config, "tts_output_dir", "data/tts"))
        self.voice_name = str(getattr(config, "tts_voice_name", "jarvis"))
        self.language = str(getattr(config, "tts_language", "en"))
        self.playback = bool(getattr(config, "tts_playback", False))
        self._providers: dict[str, TTSProvider] = {}
        self.last_result: TTSResult | None = None

    def status(self) -> str:
        lines = [
            "TTS status:",
            f"- enabled: {self.enabled}",
            f"- auto speak: {self.auto_speak}",
            f"- preferred provider: {self.provider_name}",
            f"- fallback providers: {', '.join(self.fallback_providers) if self.fallback_providers else 'none'}",
            f"- voice name: {self.voice_name}",
            f"- language: {self.language}",
            f"- output dir: {self.output_dir}",
            f"- playback: {self.playback}",
            "- SaaS note: XTTS v2 is personal/non-commercial only; swap to Kokoro, ElevenLabs, or another licensed provider before SaaS.",
            "Provider checks:",
        ]
        for provider_name in self.provider_chain():
            status = self.get_provider(provider_name).status()
            lines.append(f"- {status.format_line()}")
        return "\n".join(lines)

    def providers_summary(self) -> str:
        lines = ["Available TTS provider chain:"]
        for index, provider_name in enumerate(self.provider_chain(), start=1):
            status = self.get_provider(provider_name).status()
            marker = "preferred" if index == 1 else "fallback"
            lines.append(f"{index}. {provider_name} ({marker}) - {status.format_line()}")
        lines.append("SaaS note: keep XTTS for personal local testing only; prefer Kokoro or a licensed cloud/commercial provider for SaaS.")
        return "\n".join(lines)

    def say(self, text: str, *, play_audio: bool | None = None) -> TTSResult:
        clean_text = " ".join(str(text or "").split())
        if not clean_text:
            return TTSResult.fail("No text was provided for TTS.", provider="tts_manager")
        if not self.enabled:
            return TTSResult.fail("TTS is disabled. Set JARVIS_TTS_ENABLED=true to enable voice output.", provider="tts_manager")

        self.events.emit("voice.tts_requested", source="tts.manager", message="TTS requested.", data={"chars": len(clean_text)})
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"jarvis_tts_{_timestamp_slug()}.wav"

        errors: list[str] = []
        for provider_name in self.provider_chain():
            provider = self.get_provider(provider_name)
            status = provider.status()
            if not status.available:
                errors.append(f"{provider_name}: {status.message}")
                continue
            request = TTSRequest(
                text=clean_text,
                output_path=output_path,
                voice_name=self.voice_name,
                language=self.language,
                speaker_wav=self._configured_speaker_wav(),
                play_audio=bool(self.playback if play_audio is None else play_audio),
            )
            result = provider.synthesize(request)
            if result.success:
                played = False
                if request.play_audio and result.output_path and result.output_path.suffix.lower() == ".wav":
                    played = self._play_wav(result.output_path)
                    result.played = played
                self.last_result = result
                self.events.emit(
                    "voice.speaking_finished" if played else "voice.tts_generated",
                    source="tts.manager",
                    message=result.message,
                    data={"provider": result.provider, "output_path": str(result.output_path or ""), "played": played},
                )
                return result
            errors.append(f"{provider_name}: {result.error or result.message}")

        message = "No TTS provider could generate speech. " + " | ".join(errors)
        failed = TTSResult.fail(message, provider="tts_manager", data={"errors": errors})
        self.last_result = failed
        self.events.emit("voice.tts_failed", source="tts.manager", message=message, data={"errors": errors})
        return failed

    def provider_chain(self) -> list[str]:
        return [self.provider_name] + [name for name in self.fallback_providers if name != self.provider_name]

    def get_provider(self, provider_name: str) -> TTSProvider:
        normalized = normalize_provider_name(provider_name)
        if normalized not in self._providers:
            self._providers[normalized] = create_tts_provider(normalized, self.config)
        return self._providers[normalized]

    def set_auto_speak(self, enabled: bool) -> None:
        self.auto_speak = bool(enabled)

    def _resolve_output_dir(self, value: str | Path) -> Path:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = Path(getattr(self.config, "project_root", Path.cwd())) / path
        return path

    def _configured_speaker_wav(self) -> Path | None:
        value = getattr(self.config, "tts_xtts_speaker_wav", "")
        if not value:
            return None
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = Path(getattr(self.config, "project_root", Path.cwd())) / path
        return path

    def _play_wav(self, path: Path) -> bool:
        try:
            if sys.platform.startswith("win"):
                import winsound

                self.events.emit("voice.speaking_started", source="tts.manager", message="Playing generated speech.", data={"path": str(path)})
                winsound.PlaySound(str(path), winsound.SND_FILENAME)
                return True
        except Exception as exc:
            self.events.emit("voice.playback_failed", source="tts.manager", message=str(exc), data={"path": str(path)})
        return False


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")


def format_tts_result(result: TTSResult) -> str:
    lines = [result.message]
    lines.append(f"Provider: {result.provider}")
    if result.output_path is not None:
        lines.append(f"Output: {result.output_path}")
    lines.append(f"Played: {result.played}")
    if result.error:
        lines.append(f"Error: {result.error}")
    return "\n".join(lines)
