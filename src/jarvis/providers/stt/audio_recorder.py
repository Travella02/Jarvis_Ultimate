"""Microphone recording helpers for Jarvis STT."""

from __future__ import annotations

import time
import wave
from collections import deque
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
    """Small wrapper around optional sounddevice microphone recording.

    Fixed-duration recording is useful for tests and fallback behavior. Smart
    recording uses a simple RMS/energy endpoint detector so Jarvis can stop
    listening shortly after Tanner stops speaking instead of waiting for a fixed
    4-second clip every time.
    """

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
            _write_float32_wav(output_path, audio, sample_rate=self.sample_rate, channels=self.channels)
            return AudioRecordResult.ok(
                "Microphone recording saved.",
                output_path=output_path,
                duration_seconds=elapsed,
                sample_rate=self.sample_rate,
                channels=self.channels,
                data={"requested_duration_seconds": duration_seconds, "device": self.device or "default", "listen_mode": "fixed", "stop_reason": "fixed_duration"},
            )
        except Exception as exc:
            return AudioRecordResult.fail(f"Microphone recording failed: {type(exc).__name__}: {exc}", error=f"{type(exc).__name__}: {exc}")

    def record_until_silence(
        self,
        *,
        max_duration_seconds: float,
        silence_seconds: float,
        min_record_seconds: float,
        start_timeout_seconds: float,
        energy_threshold: float,
        pre_roll_seconds: float = 0.25,
        frame_ms: int = 30,
    ) -> AudioRecordResult:
        """Record until speech ends plus a configurable silence window.

        This is intentionally dependency-light: it uses sounddevice for input and
        a simple RMS threshold for endpointing. It is not a wake word or full VAD
        system yet, but it gives Jarvis a much more natural listen → respond
        handoff than a fixed recording timer.
        """
        status = self.status()
        if not status.get("available"):
            return AudioRecordResult.fail(status["message"], error=status.get("error"), data=status)
        if max_duration_seconds <= 0:
            return AudioRecordResult.fail("Smart listen max duration must be greater than zero.")
        if silence_seconds <= 0:
            return AudioRecordResult.fail("Smart listen silence seconds must be greater than zero.")
        if min_record_seconds < 0:
            return AudioRecordResult.fail("Smart listen minimum record seconds cannot be negative.")
        if start_timeout_seconds <= 0:
            return AudioRecordResult.fail("Smart listen start timeout must be greater than zero.")
        if energy_threshold <= 0:
            return AudioRecordResult.fail("Smart listen energy threshold must be greater than zero.")

        try:
            import numpy as np
            import sounddevice as sd

            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self.output_dir / f"jarvis_mic_{_timestamp_slug()}.wav"
            frame_count = max(1, int(self.sample_rate * (int(frame_ms) / 1000.0)))
            pre_roll_frames = max(0, int(float(pre_roll_seconds) / max(frame_count / self.sample_rate, 0.001)))
            pre_roll: deque[Any] = deque(maxlen=pre_roll_frames)
            chunks: list[Any] = []
            speech_started = False
            speech_start_elapsed: float | None = None
            last_voice_elapsed: float | None = None
            voice_chunks = 0
            silence_chunks = 0
            peak_rms = 0.0
            stop_reason = "max_duration"
            started = time.perf_counter()

            with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, dtype="float32", device=self.device) as stream:
                while True:
                    data, overflowed = stream.read(frame_count)
                    now = time.perf_counter()
                    elapsed = now - started
                    rms = float(np.sqrt(np.mean(np.square(data)))) if data.size else 0.0
                    peak_rms = max(peak_rms, rms)
                    is_voice = rms >= float(energy_threshold)

                    if is_voice:
                        voice_chunks += 1
                    else:
                        silence_chunks += 1

                    if not speech_started:
                        pre_roll.append(data.copy())
                        if is_voice:
                            speech_started = True
                            speech_start_elapsed = elapsed
                            last_voice_elapsed = elapsed
                            chunks.extend(chunk.copy() for chunk in pre_roll)
                        elif elapsed >= float(start_timeout_seconds):
                            return AudioRecordResult.fail(
                                "No speech detected before smart-listen start timeout.",
                                error="No speech detected.",
                                data={
                                    "listen_mode": "smart",
                                    "stop_reason": "start_timeout",
                                    "elapsed_seconds": elapsed,
                                    "start_timeout_seconds": start_timeout_seconds,
                                    "energy_threshold": energy_threshold,
                                    "peak_rms": peak_rms,
                                    "device": self.device or "default",
                                },
                            )
                    else:
                        chunks.append(data.copy())
                        if is_voice:
                            last_voice_elapsed = elapsed
                        quiet_for = elapsed - (last_voice_elapsed or elapsed)
                        if elapsed >= float(min_record_seconds) and quiet_for >= float(silence_seconds):
                            stop_reason = "silence_detected"
                            break

                    if elapsed >= float(max_duration_seconds):
                        stop_reason = "max_duration"
                        break

            if not speech_started or not chunks:
                return AudioRecordResult.fail(
                    "No speech detected during smart listen.",
                    error="No speech detected.",
                    data={
                        "listen_mode": "smart",
                        "stop_reason": "no_speech",
                        "max_duration_seconds": max_duration_seconds,
                        "energy_threshold": energy_threshold,
                        "peak_rms": peak_rms,
                        "device": self.device or "default",
                    },
                )

            audio = np.concatenate(chunks, axis=0)
            _write_float32_wav(output_path, audio, sample_rate=self.sample_rate, channels=self.channels)
            actual_duration = float(len(audio) / self.sample_rate)
            elapsed_wall = time.perf_counter() - started
            return AudioRecordResult.ok(
                "Microphone smart-listen recording saved.",
                output_path=output_path,
                duration_seconds=actual_duration,
                sample_rate=self.sample_rate,
                channels=self.channels,
                data={
                    "listen_mode": "smart",
                    "stop_reason": stop_reason,
                    "elapsed_wall_seconds": elapsed_wall,
                    "max_duration_seconds": max_duration_seconds,
                    "silence_seconds": silence_seconds,
                    "min_record_seconds": min_record_seconds,
                    "start_timeout_seconds": start_timeout_seconds,
                    "energy_threshold": energy_threshold,
                    "pre_roll_seconds": pre_roll_seconds,
                    "frame_ms": frame_ms,
                    "speech_started": True,
                    "speech_start_elapsed": speech_start_elapsed,
                    "last_voice_elapsed": last_voice_elapsed,
                    "voice_chunks": voice_chunks,
                    "silence_chunks": silence_chunks,
                    "peak_rms": peak_rms,
                    "device": self.device or "default",
                },
            )
        except Exception as exc:
            return AudioRecordResult.fail(f"Smart microphone recording failed: {type(exc).__name__}: {exc}", error=f"{type(exc).__name__}: {exc}")


def _write_float32_wav(output_path: Path, audio: Any, *, sample_rate: int, channels: int) -> None:
    import numpy as np

    pcm = np.clip(audio, -1.0, 1.0)
    pcm = (pcm * 32767.0).astype(np.int16)
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm.tobytes())


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
    mode = result.data.get("listen_mode")
    if mode:
        lines.append(f"Listen mode: {mode}")
    stop_reason = result.data.get("stop_reason")
    if stop_reason:
        lines.append(f"Stop reason: {stop_reason}")
    silence_seconds = result.data.get("silence_seconds")
    if silence_seconds is not None:
        lines.append(f"Silence stop: {float(silence_seconds):.2f}s")
    if result.error:
        lines.append(f"Error: {result.error}")
    return "\n".join(lines)


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
