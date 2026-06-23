import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from jarvis.providers.stt.base import STTRequest
from jarvis.providers.stt.factory import normalize_provider_name, parse_fallback_chain
from jarvis.providers.stt.manager import STTManager
from jarvis.providers.stt.mock_provider import MockSTTProvider


class TestSTTProviders(unittest.TestCase):
    def test_mock_provider_transcribes_existing_audio_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            audio = Path(tmp) / "sample.wav"
            audio.write_bytes(b"fake wav")
            provider = MockSTTProvider(text="hello sir")
            result = provider.transcribe(STTRequest(audio_path=audio, language="en"))
            self.assertTrue(result.success)
            self.assertEqual(result.text, "hello sir")
            self.assertEqual(result.provider, "mock")

    def test_mock_provider_rejects_missing_audio_path(self):
        provider = MockSTTProvider()
        result = provider.transcribe(STTRequest(audio_path=Path("missing.wav")))
        self.assertFalse(result.success)
        self.assertIn("does not exist", result.message)

    def test_provider_name_and_fallback_parsing(self):
        self.assertEqual(normalize_provider_name("whisper"), "faster_whisper")
        self.assertEqual(normalize_provider_name("faster-whisper"), "faster_whisper")
        self.assertEqual(normalize_provider_name("anything"), "mock")
        self.assertEqual(parse_fallback_chain("mock,whisper,mock"), ["mock", "faster_whisper"])

    def test_manager_transcribes_file_with_mock_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            audio = root / "sample.wav"
            audio.write_bytes(b"fake wav")
            config = SimpleNamespace(
                project_root=root,
                stt_enabled=True,
                stt_provider="mock",
                stt_fallback_providers="",
                stt_mock_text="test transcript",
                stt_output_dir="data/stt",
                stt_language="en",
                stt_record_seconds=1.0,
                stt_sample_rate=16000,
                stt_channels=1,
                stt_microphone_device="",
            )
            manager = STTManager(config)
            result = manager.transcribe_file(audio)
            self.assertTrue(result.success)
            self.assertEqual(result.text, "test transcript")
            self.assertIn("mock", manager.providers_summary())
            self.assertIn("final success: True", manager.format_debug_last())


if __name__ == "__main__":
    unittest.main()
