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
                        "JARVIS_STT_LISTEN_MODE=smart",
                        "JARVIS_STT_MAX_LISTEN_SECONDS=7.5",
                        "JARVIS_STT_SILENCE_SECONDS=0.8",
                        "JARVIS_STT_MIN_RECORD_SECONDS=0.3",
                        "JARVIS_STT_START_TIMEOUT_SECONDS=4.5",
                        "JARVIS_STT_ENERGY_THRESHOLD=0.01",
                        "JARVIS_STT_PRE_ROLL_SECONDS=0.2",
                        "JARVIS_STT_FRAME_MS=20",
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
            self.assertEqual(config.stt_listen_mode, "smart")
            self.assertEqual(config.stt_max_listen_seconds, 7.5)
            self.assertEqual(config.stt_silence_seconds, 0.8)
            self.assertEqual(config.stt_min_record_seconds, 0.3)
            self.assertEqual(config.stt_start_timeout_seconds, 4.5)
            self.assertEqual(config.stt_energy_threshold, 0.01)
            self.assertEqual(config.stt_pre_roll_seconds, 0.2)
            self.assertEqual(config.stt_frame_ms, 20)
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
                        "    listen_mode: smart",
                        "    max_listen_seconds: 6.0",
                        "    silence_seconds: 0.75",
                    ]
                ),
                encoding="utf-8",
            )
            config = JarvisConfig.from_project_root(root)
            self.assertEqual(config.stt_provider, "mock")
            self.assertEqual(config.stt_model, "tiny.en")
            self.assertEqual(config.stt_record_seconds, 2.0)
            self.assertEqual(config.stt_listen_mode, "smart")
            self.assertEqual(config.stt_max_listen_seconds, 6.0)
            self.assertEqual(config.stt_silence_seconds, 0.75)


if __name__ == "__main__":
    unittest.main()
