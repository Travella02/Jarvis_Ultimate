from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.providers.tts.manager import TTSManager


def make_config(root: Path) -> SimpleNamespace:
    return SimpleNamespace(
        project_root=root,
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
        tts_xtts_speaker_wav="assets/voices/jarvis_reference.wav",
        tts_xtts_model_name="tts_models/multilingual/multi-dataset/xtts_v2",
        tts_use_gpu=False,
        tts_device="auto",
    )


class TestTTSKokoroDefault(unittest.TestCase):
    def test_kokoro_is_default_and_xtts_is_not_in_chain(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TTSManager(make_config(Path(temp_dir)))

            self.assertEqual(manager.provider_name, "kokoro")
            self.assertEqual(manager.provider_chain(), ["kokoro", "mock"])
            self.assertNotIn("xtts", manager.provider_chain())
            self.assertIn("Kokoro voice", manager.status())

    def test_can_switch_kokoro_voice_for_runtime_session(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = TTSManager(make_config(Path(temp_dir)))

            result = manager.set_kokoro_voice("af_bella")

            self.assertTrue(result.success)
            self.assertEqual(manager.kokoro_voice, "af_bella")
            self.assertIn("af_bella", manager.format_kokoro_current_voice())
            self.assertIn("af_bella (current)", manager.format_kokoro_voices())


if __name__ == "__main__":
    unittest.main()
