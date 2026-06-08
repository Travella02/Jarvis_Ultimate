from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.core.config import JarvisConfig


class TestTTSConfig(unittest.TestCase):
    def _make_root(self, env_text: str = "", providers_text: str | None = None) -> Path:
        root = Path(tempfile.mkdtemp())
        config_dir = root / "config"
        config_dir.mkdir()
        (config_dir / "providers.yaml").write_text(
            providers_text
            or "providers:\n  llm:\n    default: mock\n  tts:\n    default: kokoro\n    fallback_providers: mock\n    output_dir: data/tts\n",
            encoding="utf-8",
        )
        (root / ".env").write_text(env_text, encoding="utf-8")
        return root

    def test_reads_tts_values_from_providers_yaml(self):
        root = self._make_root()
        with patch.dict(os.environ, {}, clear=True):
            config = JarvisConfig.from_project_root(root)

        self.assertEqual(config.tts_provider, "kokoro")
        self.assertEqual(config.tts_fallback_providers, "mock")
        self.assertEqual(config.tts_output_dir, "data/tts")
        self.assertTrue(config.tts_enabled)

    def test_project_env_overrides_tts_values(self):
        root = self._make_root(
            "JARVIS_TTS_PROVIDER=kokoro\n"
            "JARVIS_TTS_FALLBACK_PROVIDERS=mock\n"
            "JARVIS_TTS_USE_GPU=false\n"
            "JARVIS_TTS_AUTO_SPEAK=true\n"
            "JARVIS_TTS_XTTS_SPEAKER_WAV=assets/voices/custom.wav\n"
        )
        with patch.dict(os.environ, {}, clear=True):
            config = JarvisConfig.from_project_root(root)

        self.assertEqual(config.tts_provider, "kokoro")
        self.assertEqual(config.tts_fallback_providers, "mock")
        self.assertFalse(config.tts_use_gpu)
        self.assertTrue(config.tts_auto_speak)
        self.assertEqual(config.tts_xtts_speaker_wav, "assets/voices/custom.wav")


if __name__ == "__main__":
    unittest.main()
