import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from jarvis.providers.stt.audio_recorder import AudioRecordResult, format_record_result
from jarvis.providers.stt.manager import STTManager
from jarvis.clients.cli.cli_client import _parse_stt_listen_command


class FakeRecorder:
    def __init__(self, audio_path: Path):
        self.audio_path = audio_path
        self.smart_calls = []
        self.fixed_calls = []

    def status(self):
        return {"available": True, "ready": True, "message": "fake recorder ready"}

    def record_until_silence(self, **kwargs):
        self.smart_calls.append(kwargs)
        self.audio_path.write_bytes(b"fake wav")
        return AudioRecordResult.ok(
            "Microphone smart-listen recording saved.",
            output_path=self.audio_path,
            duration_seconds=1.15,
            sample_rate=16000,
            channels=1,
            data={"listen_mode": "smart", "stop_reason": "silence_detected", "silence_seconds": kwargs.get("silence_seconds"), "elapsed_wall_seconds": 1.20, "peak_rms": 0.05},
        )

    def record(self, *, duration_seconds: float):
        self.fixed_calls.append(duration_seconds)
        self.audio_path.write_bytes(b"fake wav")
        return AudioRecordResult.ok(
            "Microphone recording saved.",
            output_path=self.audio_path,
            duration_seconds=duration_seconds,
            sample_rate=16000,
            channels=1,
            data={"listen_mode": "fixed", "stop_reason": "fixed_duration"},
        )


def _config(root: Path, *, listen_mode: str = "smart"):
    return SimpleNamespace(
        project_root=root,
        stt_enabled=True,
        stt_provider="mock",
        stt_fallback_providers="",
        stt_mock_text="hello sir",
        stt_output_dir="data/stt",
        stt_language="en",
        stt_record_seconds=2.0,
        stt_listen_mode=listen_mode,
        stt_max_listen_seconds=8.0,
        stt_silence_seconds=0.8,
        stt_min_record_seconds=0.35,
        stt_start_timeout_seconds=5.0,
        stt_energy_threshold=0.012,
        stt_pre_roll_seconds=0.25,
        stt_frame_ms=30,
        stt_sample_rate=16000,
        stt_channels=1,
        stt_microphone_device="",
    )


class TestSTTLowLatencyListen(unittest.TestCase):
    def test_manager_uses_smart_endpointing_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "smart.wav"
            recorder = FakeRecorder(audio)
            manager = STTManager(_config(root, listen_mode="smart"), recorder=recorder)
            result = manager.listen_once()
            self.assertTrue(result.success)
            self.assertEqual(result.text, "hello sir")
            self.assertEqual(len(recorder.smart_calls), 1)
            self.assertEqual(recorder.smart_calls[0]["silence_seconds"], 0.8)
            self.assertEqual(recorder.fixed_calls, [])
            debug = manager.format_debug_last()
            self.assertIn("Listen mode: smart", debug)
            self.assertIn("Stop reason: silence_detected", debug)

    def test_manager_can_force_fixed_listen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "fixed.wav"
            recorder = FakeRecorder(audio)
            manager = STTManager(_config(root, listen_mode="smart"), recorder=recorder)
            result = manager.listen_once(mode="fixed", duration_seconds=1.5)
            self.assertTrue(result.success)
            self.assertEqual(recorder.fixed_calls, [1.5])
            self.assertEqual(recorder.smart_calls, [])

    def test_manager_allows_one_off_silence_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "smart_override.wav"
            recorder = FakeRecorder(audio)
            manager = STTManager(_config(root, listen_mode="smart"), recorder=recorder)
            result = manager.listen_once(mode="smart", duration_seconds=5.0, silence_seconds=0.6)
            self.assertTrue(result.success)
            self.assertEqual(recorder.smart_calls[0]["max_duration_seconds"], 5.0)
            self.assertEqual(recorder.smart_calls[0]["silence_seconds"], 0.6)

    def test_parse_low_latency_listen_commands(self):
        self.assertEqual(_parse_stt_listen_command("listen once"), {"mode": None, "duration_seconds": None, "silence_seconds": None})
        self.assertEqual(_parse_stt_listen_command("listen fixed 2"), {"mode": "fixed", "duration_seconds": 2.0, "silence_seconds": None})
        self.assertEqual(_parse_stt_listen_command("listen smart max 6 silence 0.8"), {"mode": "smart", "duration_seconds": 6.0, "silence_seconds": 0.8})
        self.assertIsNone(_parse_stt_listen_command("listen to music"))

    def test_format_record_result_shows_endpointing_details(self):
        result = AudioRecordResult.ok(
            "Microphone smart-listen recording saved.",
            output_path=Path("data/stt/sample.wav"),
            duration_seconds=1.25,
            sample_rate=16000,
            channels=1,
            data={"listen_mode": "smart", "stop_reason": "silence_detected", "silence_seconds": 0.9},
        )
        text = format_record_result(result)
        self.assertIn("Listen mode: smart", text)
        self.assertIn("Stop reason: silence_detected", text)
        self.assertIn("Silence stop: 0.90s", text)


if __name__ == "__main__":
    unittest.main()
