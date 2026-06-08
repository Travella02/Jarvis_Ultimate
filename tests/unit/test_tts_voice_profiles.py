from pathlib import Path
import sys
import tempfile
import unittest
import wave
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
        tts_voice_profiles_dir="data/tts/voices",
        tts_language="en",
        tts_playback=False,
        tts_xtts_speaker_wav="assets/voices/jarvis_reference.wav",
        tts_xtts_model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        tts_use_gpu=True,
        tts_device="cuda",
    )


def write_test_wav(path: Path, *, seconds: float = 1.0, rate: int = 16000, channels: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = int(seconds * rate)
    silence = (b"\x00\x00" * channels) * frames
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(silence)


class FakeFailProvider:
    provider_name = "xtts"

    def status(self) -> TTSProviderStatus:
        return TTSProviderStatus(name="xtts", available=True, ready=True, message="fake failing xtts")

    def synthesize(self, request: TTSRequest) -> TTSResult:
        return TTSResult.fail("XTTS failed while generating speech.", provider="xtts", error="FakeError: boom", data={"exception_type": "FakeError", "traceback": "fake stack"})


class TestTTSVoiceProfiles(unittest.TestCase):
    def test_import_voice_profile_copies_reference_and_activates_it(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "voice.wav"
            write_test_wav(source)
            manager = TTSManager(make_config(root, provider="mock"))

            result = manager.import_voice_profile("Me Voice", source)

            self.assertTrue(result.success)
            self.assertEqual(manager.voice_name, "me_voice")
            self.assertTrue((root / "data" / "tts" / "voices" / "me_voice" / "reference.wav").exists())
            self.assertIn("me_voice", manager.format_voice_profiles())

    def test_use_voice_profile_rejects_missing_voice(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TTSManager(make_config(Path(temp_dir)))

            result = manager.use_voice_profile("missing")

            self.assertFalse(result.success)
            self.assertIn("not ready", result.message)

    def test_direct_xtts_failure_is_available_in_debug_last(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "voice.wav"
            write_test_wav(source)
            manager = TTSManager(make_config(root, provider="xtts"))
            manager.import_voice_profile("jarvis", source)
            manager._providers["xtts"] = FakeFailProvider()

            result = manager.say("hello", provider_override="xtts", allow_fallback=False)
            debug = manager.format_debug_last()

            self.assertFalse(result.success)
            self.assertIn("FakeError", debug)
            self.assertIn("xtts", debug)


if __name__ == "__main__":
    unittest.main()
