"""Microphone recording helpers for Jarvis STT."""

from __future__ import annotations

import time
import wave
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class AudioRecordResult:
    success: bool
    message: str
    output_path: Path | None = None
    duration_seconds: float | None = None
    sample_rate: int | None = None
    channels: int | None = None
    error: str | None = None
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def ok(cls, message: str, *, output_path: Path, duration_seconds: float, sample_rate: int, channels: int, data: dict[str, Any] | None = None) -> "AudioRecordResult":
        return cls(True, message, output_path=output_path, duration_seconds=duration_seconds, sample_rate=sample_rate, channels=channels, data=data or {})

    @classmethod
    def fail(cls, message: str, *, error: str | None = None, data: dict[str, Any] | None = None) -> "AudioRecordResult":
        return cls(False, message, error=error or message, data=data or {})


class MicrophoneRecorder:
    """Small wrapper around optional sounddevice microphone recording."""

    def __init__(self, *, output_dir: Path, sample_rate: int = 16000, channels: int = 1, device: str | None = None) -> None:
        self.output_dir = Path(output_dir)
        self.sample_rate = int(sample_rate)
        self.channels = int(channels)
        self.device = str(device or "").strip() or None

    def status(self) -> dict[str, Any]:
        try:
            import sounddevice as sd  # noqa: F401
            import numpy as np  # noqa: F401
        except Exception as exc:
            return {
                "available": False,
                "ready": False,
                "message": "Microphone recording dependencies are not installed. Run: python -m pip install -r requirements-stt.txt",
                "error": f"{type(exc).__name__}: {exc}",
            }
        return {
            "available": True,
            "ready": True,
            "message": f"sounddevice ready, sample_rate={self.sample_rate}, channels={self.channels}, device={self.device or 'default'}",
        }

    def record(self, *, duration_seconds: float) -> AudioRecordResult:
        status = self.status()
        if not status.get("available"):
            return AudioRecordResult.fail(status["message"], error=status.get("error"), data=status)
        if duration_seconds <= 0:
            return AudioRecordResult.fail("Recording duration must be greater than zero.")

        try:
            import numpy as np
            import sounddevice as sd

            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self.output_dir / f"jarvis_mic_{_timestamp_slug()}.wav"
            frames = int(float(duration_seconds) * self.sample_rate)
            started = time.perf_counter()
            audio = sd.rec(frames, samplerate=self.sample_rate, channels=self.channels, dtype="float32", device=self.device)
            sd.wait()
            elapsed = time.perf_counter() - started
            pcm = np.clip(audio, -1.0, 1.0)
            pcm = (pcm * 32767.0).astype(np.int16)
            with wave.open(str(output_path), "wb") as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(pcm.tobytes())
            return AudioRecordResult.ok(
                "Microphone recording saved.",
                output_path=output_path,
                duration_seconds=elapsed,
                sample_rate=self.sample_rate,
                channels=self.channels,
                data={"requested_duration_seconds": duration_seconds, "device": self.device or "default"},
            )
        except Exception as exc:
            return AudioRecordResult.fail(f"Microphone recording failed: {type(exc).__name__}: {exc}", error=f"{type(exc).__name__}: {exc}")


def _display_path(path: Path) -> str:
    """Return a stable user/test display path across Windows, macOS, and Linux."""
    return str(path).replace("\\", "/")


def format_record_result(result: AudioRecordResult) -> str:
    lines = [result.message]
    if result.output_path:
        lines.append(f"Output: {_display_path(result.output_path)}")
    if result.duration_seconds is not None:
        lines.append(f"Duration: {result.duration_seconds:.2f}s")
    if result.sample_rate is not None:
        lines.append(f"Sample rate: {result.sample_rate}")
    if result.channels is not None:
        lines.append(f"Channels: {result.channels}")
    if result.error:
        lines.append(f"Error: {result.error}")
    return "\n".join(lines)


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
