from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.providers.tts.base import TTSRequest
from jarvis.providers.tts.factory import normalize_provider_name, parse_fallback_chain
from jarvis.providers.tts.manager import TTSManager
from jarvis.providers.tts.mock_provider import MockTTSProvider


class TestTTSProviders(unittest.TestCase):
    def test_mock_provider_writes_placeholder(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "voice.wav"
            result = MockTTSProvider().synthesize(TTSRequest(text="hello", output_path=output))

            self.assertTrue(result.success)
            self.assertEqual(result.provider, "mock")
            self.assertTrue(result.output_path.exists())
            self.assertEqual(result.output_path.read_text(encoding="utf-8"), "hello")

    def test_provider_name_and_fallback_parsing(self):
        self.assertEqual(normalize_provider_name("coqui-xtts"), "xtts")
        self.assertEqual(normalize_provider_name("kokoro_tts"), "kokoro")
        self.assertEqual(parse_fallback_chain("kokoro,mock,kokoro"), ["kokoro", "mock"])

    def test_manager_uses_mock_fallback_when_kokoro_unavailable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            config = SimpleNamespace(
                project_root=Path(temp_dir),
                tts_enabled=True,
                tts_auto_speak=False,
                tts_provider="kokoro",
                tts_fallback_providers="mock",
                tts_output_dir="data/tts",
                tts_voice_name="jarvis",
                tts_voice_profiles_dir="data/tts/voices",
                tts_language="en",
                tts_playback=False,
                tts_kokoro_voice="af_heart",
                tts_kokoro_lang_code="a",
                tts_xtts_speaker_wav="assets/voices/missing.wav",
                tts_xtts_model_name="tts_models/multilingual/multi-dataset/xtts_v2",
                tts_use_gpu=False,
                tts_device="auto",
            )
            manager = TTSManager(config)
            with patch(
                "jarvis.providers.tts.kokoro_provider.KokoroTTSProvider._check_imports",
                return_value=(False, "Kokoro intentionally unavailable for fallback test."),
            ):
                result = manager.say("hello from fallback")

            self.assertTrue(result.success)
            self.assertEqual(result.provider, "mock")
            self.assertIn("preferred provider: kokoro", manager.status().lower())
            self.assertIn("fallback providers: mock", manager.status().lower())


if __name__ == "__main__":
    unittest.main()
