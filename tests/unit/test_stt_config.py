import tempfile
import unittest
from pathlib import Path

from jarvis.core.config import JarvisConfig


class TestSTTConfig(unittest.TestCase):
    def test_reads_stt_settings_from_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config" / "providers.yaml").write_text("providers:\n  stt:\n    default: mock\n", encoding="utf-8")
            (root / ".env").write_text(
                "\n".join(
                    [
                        "JARVIS_STT_PROVIDER=faster_whisper",
                        "JARVIS_STT_MODEL=tiny.en",
                        "JARVIS_STT_DEVICE=cpu",
                        "JARVIS_STT_COMPUTE_TYPE=int8",
                        "JARVIS_STT_RECORD_SECONDS=3.5",
                        "JARVIS_STT_SAMPLE_RATE=16000",
                        "JARVIS_STT_CHANNELS=1",
                    ]
                ),
                encoding="utf-8",
            )
            config = JarvisConfig.from_project_root(root)
            self.assertEqual(config.stt_provider, "faster_whisper")
            self.assertEqual(config.stt_model, "tiny.en")
            self.assertEqual(config.stt_device, "cpu")
            self.assertEqual(config.stt_compute_type, "int8")
            self.assertEqual(config.stt_record_seconds, 3.5)
            self.assertEqual(config.stt_sample_rate, 16000)
            self.assertEqual(config.stt_channels, 1)

    def test_reads_stt_settings_from_provider_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config" / "providers.yaml").write_text(
                "\n".join(
                    [
                        "providers:",
                        "  stt:",
                        "    default: mock",
                        "    fallback_providers: mock",
                        "    model: tiny.en",
                        "    record_seconds: 2.0",
                    ]
                ),
                encoding="utf-8",
            )
            config = JarvisConfig.from_project_root(root)
            self.assertEqual(config.stt_provider, "mock")
            self.assertEqual(config.stt_model, "tiny.en")
            self.assertEqual(config.stt_record_seconds, 2.0)


if __name__ == "__main__":
    unittest.main()
