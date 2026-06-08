from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.providers.tts.base import TTSProviderStatus, TTSRequest, TTSResult
from jarvis.providers.tts.manager import TTSManager


def make_config(root: Path, *, provider: str = "mock") -> SimpleNamespace:
    return SimpleNamespace(
        project_root=root,
        tts_enabled=True,
        tts_auto_speak=False,
        tts_provider=provider,
        tts_fallback_providers="mock",
        tts_output_dir="data/tts",
        tts_voice_name="jarvis",
        tts_language="en",
        tts_playback=False,
        tts_xtts_speaker_wav="assets/voices/jarvis_reference.wav",
        tts_xtts_model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        tts_use_gpu=True,
        tts_device="cuda",
    )


class FakeWavProvider:
    provider_name = "mock"

    def status(self) -> TTSProviderStatus:
        return TTSProviderStatus(name="mock", available=True, ready=True, message="fake wav provider")

    def synthesize(self, request: TTSRequest) -> TTSResult:
        request.output_path.parent.mkdir(parents=True, exist_ok=True)
        request.output_path.write_bytes(b"RIFFxxxxWAVEfmt ")
        return TTSResult.ok("Fake WAV generated.", provider="mock", output_path=request.output_path)


class TestTTSPlaybackReference(unittest.TestCase):
    def test_playback_flag_can_force_playback_for_one_say_call(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager = TTSManager(make_config(root))
            manager._providers["mock"] = FakeWavProvider()
            manager._play_wav = lambda path: True  # type: ignore[method-assign]

            result = manager.say("hello", play_audio=True)

            self.assertTrue(result.success)
            self.assertTrue(result.played)
            self.assertTrue(result.output_path.exists())

    def test_play_last_reports_missing_previous_audio(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TTSManager(make_config(Path(temp_dir)))
            result = manager.play_last()

            self.assertFalse(result.success)
            self.assertIn("No generated TTS audio", result.message)

    def test_play_last_rejects_non_wav_placeholder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager = TTSManager(make_config(root))
            first = manager.say("hello", play_audio=False)

            played = manager.play_last()

            self.assertTrue(first.success)
            self.assertFalse(played.success)
            self.assertIn("not a playable WAV", played.message)

    def test_play_last_uses_previous_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manager = TTSManager(make_config(root))
            manager._providers["mock"] = FakeWavProvider()
            manager._play_wav = lambda path: True  # type: ignore[method-assign]
            first = manager.say("hello", play_audio=False)

            played = manager.play_last()

            self.assertTrue(first.success)
            self.assertTrue(played.success)
            self.assertTrue(played.played)
            self.assertEqual(played.output_path, first.output_path)

    def test_reference_status_and_import(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "sample.wav"
            source.write_bytes(b"RIFFxxxxWAVEfmt ")
            manager = TTSManager(make_config(root, provider="xtts"))

            before = manager.speaker_reference_status()
            result = manager.set_speaker_wav(source, copy_to_default=True)
            after = manager.speaker_reference_status()

            self.assertFalse(before["ready"])
            self.assertTrue(result.success)
            self.assertTrue(after["ready"])
            self.assertEqual(manager.speaker_wav, root / "assets" / "voices" / "jarvis_reference.wav")
            self.assertTrue((root / "assets" / "voices" / "jarvis_reference.wav").exists())

    def test_reference_rejects_non_wav(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "sample.mp3"
            source.write_text("fake", encoding="utf-8")
            manager = TTSManager(make_config(root))

            result = manager.set_speaker_wav(source)

            self.assertFalse(result.success)
            self.assertIn(".wav", result.message)


if __name__ == "__main__":
    unittest.main()
