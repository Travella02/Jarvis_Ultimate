"""TTS manager for provider selection, Kokoro voices, fallback, and playback.

XTTS helper methods are kept as an experimental personal/local path, but 0.0.7c
makes Kokoro the default provider so normal Jarvis setup stays simple and
closer to future SaaS requirements.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jarvis.core.events import EventBus
from jarvis.providers.tts.base import TTSProvider, TTSRequest, TTSResult
from jarvis.providers.tts.factory import create_tts_provider, normalize_provider_name, parse_fallback_chain


_SAFE_VOICE_RE = re.compile(r"[^a-z0-9_-]+")

KOKORO_COMMON_VOICES = [
    "af_heart",
    "af_alloy",
    "af_aoede",
    "af_bella",
    "af_jessica",
    "af_kore",
    "af_nicole",
    "af_nova",
    "af_river",
    "af_sarah",
    "af_sky",
    "am_adam",
    "am_echo",
    "am_eric",
    "am_fenrir",
    "am_liam",
    "am_michael",
    "am_onyx",
    "am_puck",
    "am_santa",
    "bf_alice",
    "bf_emma",
    "bf_isabella",
    "bf_lily",
    "bm_daniel",
    "bm_fable",
    "bm_george",
    "bm_lewis",
]


class TTSManager:
    """Coordinates swappable TTS providers without coupling them to the brain."""

    def __init__(self, config: Any, *, events: EventBus | None = None) -> None:
        self.config = config
        self.events = events or EventBus()
        self.enabled = bool(getattr(config, "tts_enabled", True))
        self.auto_speak = bool(getattr(config, "tts_auto_speak", False))
        self.provider_name = normalize_provider_name(getattr(config, "tts_provider", "kokoro"))
        fallback_value = getattr(config, "tts_fallback_providers", "mock")
        self.fallback_providers = [name for name in parse_fallback_chain(fallback_value) if name != self.provider_name]
        if "mock" not in self.fallback_providers:
            self.fallback_providers.append("mock")
        self.project_root = Path(getattr(config, "project_root", Path.cwd()))
        self.output_dir = self._resolve_project_path(getattr(config, "tts_output_dir", "data/tts"))
        self.voice_name = self._normalize_voice_name(str(getattr(config, "tts_voice_name", "jarvis")))
        self.language = str(getattr(config, "tts_language", "en"))
        self.kokoro_voice = str(getattr(config, "tts_kokoro_voice", "af_heart")).strip() or "af_heart"
        self.playback = bool(getattr(config, "tts_playback", False))
        self.voice_profiles_dir = self._resolve_project_path(getattr(config, "tts_voice_profiles_dir", "data/tts/voices"))
        configured_speaker = self._resolve_speaker_wav(getattr(config, "tts_xtts_speaker_wav", "assets/voices/jarvis_reference.wav"))
        profile_speaker = self.profile_reference_path(self.voice_name)
        self.speaker_wav = profile_speaker if profile_speaker.exists() else configured_speaker
        self._providers: dict[str, TTSProvider] = {}
        self.last_result: TTSResult | None = None
        self.last_attempts: list[dict[str, Any]] = []

    def status(self) -> str:
        provider_chain = self.provider_chain()
        lines = [
            "TTS status:",
            f"- enabled: {self.enabled}",
            f"- auto speak: {self.auto_speak}",
            f"- preferred provider: {self.provider_name}",
            f"- fallback providers: {', '.join(self.fallback_providers) if self.fallback_providers else 'none'}",
            f"- assistant voice name: {self.voice_name}",
            f"- Kokoro voice: {self.kokoro_voice}",
            f"- language: {self.language}",
            f"- output dir: {self.output_dir}",
            f"- playback: {self.playback}",
            f"- playback support: {self._playback_support_label()}",
            "- SaaS note: Kokoro is the default local provider. XTTS is experimental/personal-only and disabled unless explicitly selected.",
        ]
        if "xtts" in provider_chain:
            reference = self.speaker_reference_status()
            lines.extend([
                f"- XTTS reference WAV: {reference['path']}",
                f"- XTTS reference ready: {reference['ready']} ({reference['message']})",
            ])
        lines.append("Provider checks:")
        for provider_name in provider_chain:
            status = self.get_provider(provider_name).status()
            lines.append(f"- {status.format_line()}")
        return "\n".join(lines)

    def providers_summary(self) -> str:
        lines = ["Available TTS provider chain:"]
        for index, provider_name in enumerate(self.provider_chain(), start=1):
            status = self.get_provider(provider_name).status()
            marker = "preferred" if index == 1 else "fallback"
            lines.append(f"{index}. {provider_name} ({marker}) - {status.format_line()}")
        lines.append("SaaS note: Kokoro is the default local TTS path. XTTS remains experimental/personal-only; ElevenLabs or another licensed provider can be added later.")
        return "\n".join(lines)

    def say(
        self,
        text: str,
        *,
        play_audio: bool | None = None,
        voice_name: str | None = None,
        provider_override: str | None = None,
        allow_fallback: bool = True,
    ) -> TTSResult:
        clean_text = " ".join(str(text or "").split())
        if not clean_text:
            return TTSResult.fail("No text was provided for TTS.", provider="tts_manager")
        if not self.enabled:
            return TTSResult.fail("TTS is disabled. Set JARVIS_TTS_ENABLED=true to enable voice output.", provider="tts_manager")

        selected_voice = self._normalize_voice_name(voice_name or self.voice_name)
        selected_speaker = self.speaker_wav_for_voice(selected_voice)
        should_play = bool(self.playback if play_audio is None else play_audio)
        selected_chain = self.provider_chain(provider_override=provider_override, allow_fallback=allow_fallback)
        self.events.emit(
            "voice.tts_requested",
            source="tts.manager",
            message="TTS requested.",
            data={"chars": len(clean_text), "play_audio": should_play, "voice_name": selected_voice, "provider_chain": selected_chain},
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_path = self.output_dir / f"jarvis_tts_{selected_voice}_{_timestamp_slug()}.wav"

        errors: list[str] = []
        attempts: list[dict[str, Any]] = []
        self.last_attempts = []
        for provider_name in selected_chain:
            provider = self.get_provider(provider_name)
            if provider_name == "xtts":
                self._update_provider_speaker("xtts", selected_speaker)
            status = provider.status()
            attempt: dict[str, Any] = {
                "provider": provider_name,
                "available": status.available,
                "ready": status.ready,
                "status_message": status.message,
                "voice_name": selected_voice,
                "speaker_wav": str(selected_speaker) if selected_speaker else "",
            }
            if not status.available:
                error = f"{provider_name}: {status.message}"
                errors.append(error)
                attempt.update({"success": False, "error": status.message})
                attempts.append(attempt)
                continue
            request = TTSRequest(
                text=clean_text,
                output_path=output_path,
                voice_name=selected_voice,
                language=self.language,
                speaker_wav=selected_speaker,
                play_audio=should_play,
                metadata={"provider_override": provider_override or "", "allow_fallback": allow_fallback},
            )
            result = provider.synthesize(request)
            attempt.update(
                {
                    "success": result.success,
                    "message": result.message,
                    "error": result.error or "",
                    "output_path": str(result.output_path or ""),
                    "data": result.data,
                }
            )
            attempts.append(attempt)
            if result.success:
                played = False
                if should_play and result.output_path and result.output_path.suffix.lower() == ".wav":
                    played = self._play_wav(result.output_path)
                    result.played = played
                result.data.setdefault("attempts", attempts)
                result.data.setdefault("voice_name", selected_voice)
                result.data.setdefault("provider_chain", selected_chain)
                self.last_result = result
                self.last_attempts = attempts
                self.events.emit(
                    "voice.speaking_finished" if played else "voice.tts_generated",
                    source="tts.manager",
                    message=result.message,
                    data={"provider": result.provider, "output_path": str(result.output_path or ""), "played": played, "voice_name": selected_voice},
                )
                return result
            errors.append(f"{provider_name}: {result.error or result.message}")

        message = "No TTS provider could generate speech. " + " | ".join(errors)
        failed = TTSResult.fail(message, provider="tts_manager", data={"errors": errors, "attempts": attempts, "voice_name": selected_voice, "provider_chain": selected_chain})
        self.last_result = failed
        self.last_attempts = attempts
        self.events.emit("voice.tts_failed", source="tts.manager", message=message, data={"errors": errors, "attempts": attempts})
        return failed

    def play_last(self) -> TTSResult:
        """Play the most recently generated WAV without regenerating speech."""
        if self.last_result is None or self.last_result.output_path is None:
            return TTSResult.fail("No generated TTS audio is available yet. Run 'tts test' or 'tts say ...' first.", provider="tts_manager")
        path = self.last_result.output_path
        if not path.exists():
            return TTSResult.fail(f"The last TTS output no longer exists: {path}", provider="tts_manager")
        if path.suffix.lower() != ".wav":
            return TTSResult.fail(f"The last TTS output is not a playable WAV file: {path}", provider="tts_manager")
        played = self._play_wav(path)
        result = TTSResult.ok(
            "Played the last generated TTS audio." if played else "Could not play the last generated TTS audio.",
            provider=self.last_result.provider,
            output_path=path,
            played=played,
            data={"source": "last_result"},
        )
        if not played:
            result.success = False
            result.error = "Playback failed or is not supported in this environment."
        return result

    def provider_chain(self, *, provider_override: str | None = None, allow_fallback: bool = True) -> list[str]:
        primary = normalize_provider_name(provider_override or self.provider_name)
        if not allow_fallback:
            return [primary]
        return [primary] + [name for name in self.fallback_providers if name != primary]

    def get_provider(self, provider_name: str) -> TTSProvider:
        normalized = normalize_provider_name(provider_name)
        if normalized not in self._providers:
            self._providers[normalized] = create_tts_provider(normalized, self.config)
            if normalized == "kokoro" and hasattr(self._providers[normalized], "voice_name"):
                setattr(self._providers[normalized], "voice_name", self.kokoro_voice)
            self._update_provider_speaker(normalized)
        return self._providers[normalized]

    def set_auto_speak(self, enabled: bool) -> None:
        self.auto_speak = bool(enabled)

    def set_playback(self, enabled: bool) -> None:
        self.playback = bool(enabled)

    # ------------------------------------------------------------------
    # Kokoro voice helpers
    # ------------------------------------------------------------------
    def set_kokoro_voice(self, voice_name: str) -> TTSResult:
        """Switch the active Kokoro voice for this runtime session."""
        selected = self._normalize_voice_name(voice_name)
        if not selected:
            return TTSResult.fail("No Kokoro voice name was provided.", provider="tts_manager")
        self.kokoro_voice = selected
        setattr(self.config, "tts_kokoro_voice", selected)
        provider = self._providers.get("kokoro")
        if provider is not None and hasattr(provider, "voice_name"):
            setattr(provider, "voice_name", selected)
        return TTSResult.ok(
            f"Kokoro voice set to '{selected}' for this runtime session.",
            provider="tts_manager",
            data={"kokoro_voice": selected, "known_voice": selected in KOKORO_COMMON_VOICES},
        )

    def format_kokoro_voices(self) -> str:
        """Return known Kokoro voice ids with the current one marked."""
        lines = [
            "Kokoro voice options:",
            f"- current Kokoro voice: {self.kokoro_voice}",
            "- use: tts voice use <voice_id>",
            "- test: tts voice test <voice_id> play",
            "- note: you may also try provider-specific voice IDs not listed here if your Kokoro install supports them.",
            "Known/common voices:",
        ]
        for voice in KOKORO_COMMON_VOICES:
            marker = " (current)" if voice == self.kokoro_voice else ""
            lines.append(f"- {voice}{marker}")
        return "\n".join(lines)

    def format_kokoro_current_voice(self) -> str:
        return "\n".join([
            "Current TTS voice:",
            f"- provider: {self.provider_name}",
            f"- assistant voice name: {self.voice_name}",
            f"- Kokoro voice: {self.kokoro_voice}",
            "- change it with: tts voice use <voice_id>",
        ])

    # ------------------------------------------------------------------
    # XTTS speaker reference and multi-voice profile helpers
    # ------------------------------------------------------------------
    def speaker_reference_status(self) -> dict[str, Any]:
        """Return status for the currently active XTTS speaker WAV."""
        return self.voice_profile_status(self.voice_name)

    def set_speaker_wav(self, path: str | Path, *, copy_to_default: bool = False) -> TTSResult:
        """Set or import the XTTS reference WAV for the current runtime session."""
        source = self._resolve_project_path(path)
        validation = self._validate_reference_wav(source)
        if not validation["ok"]:
            return TTSResult.fail(str(validation["message"]), provider="tts_manager", data={"path": str(source), "warnings": validation["warnings"]})

        target = source
        copied = False
        if copy_to_default:
            target = self.default_reference_path()
            self._copy_reference_wav(source, target)
            copied = source.resolve() != target.resolve()

        self.speaker_wav = target
        setattr(self.config, "tts_xtts_speaker_wav", str(target))
        self._update_provider_speaker("xtts", target)
        status = self.speaker_reference_status()
        message = "Imported XTTS speaker reference WAV." if copied else "XTTS speaker reference WAV set for this runtime session."
        return TTSResult.ok(message, provider="tts_manager", output_path=target, data={"reference_status": status, "copied": copied, "warnings": validation["warnings"]})

    def default_reference_path(self) -> Path:
        return self.project_root / "assets" / "voices" / "jarvis_reference.wav"

    def profile_reference_path(self, voice_name: str) -> Path:
        safe_name = self._normalize_voice_name(voice_name)
        return self.voice_profiles_dir / safe_name / "reference.wav"

    def speaker_wav_for_voice(self, voice_name: str | None = None) -> Path | None:
        safe_name = self._normalize_voice_name(voice_name or self.voice_name)
        profile_path = self.profile_reference_path(safe_name)
        if profile_path.exists():
            return profile_path
        if safe_name == self.voice_name and self.speaker_wav is not None:
            return self.speaker_wav
        return None

    def voice_profile_status(self, voice_name: str | None = None) -> dict[str, Any]:
        safe_name = self._normalize_voice_name(voice_name or self.voice_name)
        path = self.speaker_wav_for_voice(safe_name)
        if path is None:
            return {"ready": False, "voice_name": safe_name, "path": "", "message": "no speaker WAV path is configured", "warnings": []}
        validation = self._validate_reference_wav(path)
        return {
            "ready": bool(validation["ok"]),
            "voice_name": safe_name,
            "path": str(path),
            "message": str(validation["message"]),
            "warnings": list(validation["warnings"]),
            "details": validation.get("details", {}),
        }

    def list_voice_profiles(self) -> list[dict[str, Any]]:
        profiles: dict[str, dict[str, Any]] = {}
        self.voice_profiles_dir.mkdir(parents=True, exist_ok=True)
        for child in sorted(self.voice_profiles_dir.iterdir()):
            if child.is_dir():
                profiles[child.name] = self.voice_profile_status(child.name)
        if self.speaker_wav and self.speaker_wav.exists():
            profiles.setdefault(self.voice_name, self.voice_profile_status(self.voice_name))
        return list(profiles.values())

    def format_voice_profiles(self) -> str:
        profiles = self.list_voice_profiles()
        lines = ["XTTS voice profiles:", f"- current voice: {self.voice_name}", f"- profile dir: {self.voice_profiles_dir}"]
        if not profiles:
            lines.append("- no voice profiles imported yet")
            lines.append("Use: tts voice import jarvis C:\\path\\to\\reference.wav")
            return "\n".join(lines)
        for profile in profiles:
            current = " (current)" if profile["voice_name"] == self.voice_name else ""
            lines.append(f"- {profile['voice_name']}{current}: ready={profile['ready']} path={profile['path'] or '(missing)'}")
            if profile.get("warnings"):
                lines.append("  warnings: " + "; ".join(profile["warnings"]))
        return "\n".join(lines)

    def format_current_voice(self) -> str:
        status = self.voice_profile_status(self.voice_name)
        lines = [
            "Current XTTS voice profile:",
            f"- voice: {self.voice_name}",
            f"- ready: {status['ready']}",
            f"- path: {status['path'] or '(not configured)'}",
            f"- message: {status['message']}",
        ]
        warnings = status.get("warnings") or []
        if warnings:
            lines.append("- warnings: " + "; ".join(warnings))
        return "\n".join(lines)

    def import_voice_profile(self, voice_name: str, path: str | Path, *, activate: bool = True) -> TTSResult:
        safe_name = self._normalize_voice_name(voice_name)
        source = self._resolve_project_path(path)
        validation = self._validate_reference_wav(source)
        if not validation["ok"]:
            return TTSResult.fail(str(validation["message"]), provider="tts_manager", data={"voice_name": safe_name, "path": str(source), "warnings": validation["warnings"]})
        target = self.profile_reference_path(safe_name)
        self._copy_reference_wav(source, target)
        if activate:
            self.use_voice_profile(safe_name)
        return TTSResult.ok(
            f"Imported XTTS voice profile '{safe_name}'." + (" It is now the active voice." if activate else ""),
            provider="tts_manager",
            output_path=target,
            data={"voice_name": safe_name, "reference_status": self.voice_profile_status(safe_name), "warnings": validation["warnings"]},
        )

    def use_voice_profile(self, voice_name: str) -> TTSResult:
        safe_name = self._normalize_voice_name(voice_name)
        status = self.voice_profile_status(safe_name)
        if not status["ready"]:
            return TTSResult.fail(
                f"XTTS voice profile '{safe_name}' is not ready. Import a clean WAV first.",
                provider="tts_manager",
                data={"voice_name": safe_name, "status": status},
            )
        self.voice_name = safe_name
        self.speaker_wav = Path(status["path"])
        setattr(self.config, "tts_voice_name", safe_name)
        setattr(self.config, "tts_xtts_speaker_wav", str(self.speaker_wav))
        self._update_provider_speaker("xtts", self.speaker_wav)
        return TTSResult.ok(f"XTTS voice profile '{safe_name}' is now active.", provider="tts_manager", output_path=self.speaker_wav, data={"voice_name": safe_name, "status": status})

    def delete_voice_profile(self, voice_name: str) -> TTSResult:
        safe_name = self._normalize_voice_name(voice_name)
        target_dir = self.voice_profiles_dir / safe_name
        if not target_dir.exists():
            return TTSResult.fail(f"XTTS voice profile '{safe_name}' does not exist.", provider="tts_manager", data={"voice_name": safe_name})
        shutil.rmtree(target_dir)
        if safe_name == self.voice_name:
            self.speaker_wav = self._resolve_speaker_wav(getattr(self.config, "tts_xtts_speaker_wav", "assets/voices/jarvis_reference.wav"))
        return TTSResult.ok(f"Deleted XTTS voice profile '{safe_name}'.", provider="tts_manager", data={"voice_name": safe_name})

    def format_debug_last(self) -> str:
        lines = ["Last TTS debug:"]
        if self.last_result is None:
            lines.append("- no TTS request has run yet")
            return "\n".join(lines)
        lines.append(f"- final success: {self.last_result.success}")
        lines.append(f"- final provider: {self.last_result.provider}")
        lines.append(f"- final message: {self.last_result.message}")
        if self.last_result.error:
            lines.append(f"- final error: {self.last_result.error}")
        if self.last_result.output_path:
            lines.append(f"- final output: {self.last_result.output_path}")
        attempts = self.last_attempts or self.last_result.data.get("attempts", [])
        if not attempts:
            lines.append("- no provider attempts were recorded")
            return "\n".join(lines)
        lines.append("Provider attempts:")
        for index, attempt in enumerate(attempts, start=1):
            lines.append(f"{index}. {attempt.get('provider')} success={attempt.get('success')} ready={attempt.get('ready')} available={attempt.get('available')}")
            if attempt.get("status_message"):
                lines.append(f"   status: {attempt.get('status_message')}")
            if attempt.get("speaker_wav"):
                lines.append(f"   speaker_wav: {attempt.get('speaker_wav')}")
            if attempt.get("message"):
                lines.append(f"   message: {attempt.get('message')}")
            if attempt.get("error"):
                lines.append(f"   error: {attempt.get('error')}")
            data = attempt.get("data") or {}
            if data.get("exception_type"):
                lines.append(f"   exception_type: {data.get('exception_type')}")
            if data.get("traceback"):
                lines.append("   traceback:")
                for line in str(data.get("traceback")).splitlines()[-8:]:
                    lines.append(f"     {line}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal utilities
    # ------------------------------------------------------------------
    def _resolve_output_dir(self, value: str | Path) -> Path:
        return self._resolve_project_path(value)

    def _resolve_project_path(self, value: str | Path) -> Path:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = self.project_root / path
        return path

    def _resolve_speaker_wav(self, value: str | Path | None) -> Path | None:
        if not value:
            return None
        return self._resolve_project_path(value)

    def _update_provider_speaker(self, provider_name: str, speaker_wav: Path | None = None) -> None:
        provider = self._providers.get(provider_name)
        if provider is not None and hasattr(provider, "speaker_wav"):
            setattr(provider, "speaker_wav", speaker_wav or self.speaker_wav)

    def _normalize_voice_name(self, name: str | None) -> str:
        text = str(name or "jarvis").strip().lower().replace(" ", "_")
        text = _SAFE_VOICE_RE.sub("_", text).strip("_")
        return text or "jarvis"

    def _copy_reference_wav(self, source: Path, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.resolve() == target.resolve():
            return
        # Keep the original WAV exactly for now. 0.0.7b validates and warns, but
        # does not destructively resample user voice references.
        shutil.copy2(source, target)

    def _validate_reference_wav(self, path: Path) -> dict[str, Any]:
        warnings: list[str] = []
        if path.suffix.lower() != ".wav":
            return {"ok": False, "message": "XTTS reference must be a .wav file.", "warnings": warnings, "details": {"path": str(path)}}
        if not path.exists():
            return {"ok": False, "message": "XTTS reference WAV was not found.", "warnings": warnings, "details": {"path": str(path)}}
        details = self._wav_detail_dict(path)
        if not details:
            return {"ok": True, "message": "file exists, but WAV details could not be read", "warnings": ["could not read WAV metadata"], "details": {"path": str(path)}}
        duration = float(details.get("duration_seconds", 0.0))
        channels = int(details.get("channels", 0))
        sample_rate = int(details.get("sample_rate", 0))
        sample_width = int(details.get("sample_width", 0))
        if duration < 6.0:
            warnings.append("reference is short; XTTS usually works better with 10-30 seconds of clean speech")
        if channels != 1:
            warnings.append("reference is not mono; a clean mono WAV is recommended for voice cloning")
        if sample_rate < 16000:
            warnings.append("sample rate is low; 22050 Hz or 24000 Hz+ is recommended")
        if sample_width not in {2, 4}:
            warnings.append("unusual WAV bit depth; 16-bit PCM is the safest reference format")
        message = f"file exists, {duration:.1f}s, {sample_rate} Hz, {channels} channel(s)"
        return {"ok": True, "message": message, "warnings": warnings, "details": details}

    def _play_wav(self, path: Path) -> bool:
        try:
            self.events.emit("voice.speaking_started", source="tts.manager", message="Playing generated speech.", data={"path": str(path)})
            if sys.platform.startswith("win"):
                import winsound

                winsound.PlaySound(str(path), winsound.SND_FILENAME)
                return True
            if sys.platform == "darwin":
                return subprocess.run(["afplay", str(path)], check=False).returncode == 0
            for command in (["aplay", str(path)], ["paplay", str(path)], ["ffplay", "-nodisp", "-autoexit", str(path)]):
                executable = shutil.which(command[0])
                if executable:
                    return subprocess.run([executable, *command[1:]], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
        except Exception as exc:
            self.events.emit("voice.playback_failed", source="tts.manager", message=str(exc), data={"path": str(path)})
        return False

    def _playback_support_label(self) -> str:
        if sys.platform.startswith("win"):
            return "windows winsound"
        if sys.platform == "darwin":
            return "macOS afplay" if shutil.which("afplay") else "no afplay command found"
        available = [name for name in ("aplay", "paplay", "ffplay") if shutil.which(name)]
        return ", ".join(available) if available else "no supported playback command found"

    def _wav_details(self, path: Path) -> str:
        details = self._wav_detail_dict(path)
        if not details:
            return ""
        return f"{float(details['duration_seconds']):.1f}s, {details['sample_rate']} Hz, {details['channels']} channel(s)"

    def _wav_detail_dict(self, path: Path) -> dict[str, Any]:
        try:
            with wave.open(str(path), "rb") as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                duration = frames / float(rate) if rate else 0.0
                return {
                    "duration_seconds": duration,
                    "sample_rate": rate,
                    "channels": wav.getnchannels(),
                    "sample_width": wav.getsampwidth(),
                    "frames": frames,
                }
        except Exception:
            return {}


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
    warnings: list[str] = []
    data = result.data if isinstance(result.data, dict) else {}
    if isinstance(data.get("warnings"), list):
        warnings.extend(str(item) for item in data["warnings"])
    status = data.get("reference_status") if isinstance(data.get("reference_status"), dict) else {}
    if isinstance(status.get("warnings"), list):
        warnings.extend(str(item) for item in status["warnings"])
    if warnings:
        lines.append("Warnings:")
        for warning in warnings:
            lines.append(f"- {warning}")
    attempts = data.get("attempts") if isinstance(data.get("attempts"), list) else []
    failed_attempts = [attempt for attempt in attempts if not attempt.get("success")]
    if failed_attempts and result.success:
        lines.append("Fallback/debug note: one or more earlier providers failed. Run 'tts debug last' for details.")
    return "\n".join(lines)
