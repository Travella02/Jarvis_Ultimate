import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jarvis.core.config import JarvisConfig
from jarvis.providers.stt.faster_whisper_provider import FasterWhisperSTTProvider, _resolve_compute_type, stt_gpu_diagnostics
from jarvis.providers.stt.manager import STTManager


class TestSTTGPUConfig(unittest.TestCase):
    def test_reads_gpu_stt_settings_from_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config" / "providers.yaml").write_text("providers:\n  stt:\n    default: faster_whisper\n", encoding="utf-8")
            (root / ".env").write_text(
                "\n".join(
                    [
                        "JARVIS_STT_DEVICE=auto",
                        "JARVIS_STT_COMPUTE_TYPE=auto",
                        "JARVIS_STT_GPU_FALLBACK_TO_CPU=true",
                        "JARVIS_STT_DEVICE_INDEX=1",
                        "JARVIS_STT_WARMUP_ON_BOOT=true",
                    ]
                ),
                encoding="utf-8",
            )
            config = JarvisConfig.from_project_root(root)
            self.assertEqual(config.stt_device, "auto")
            self.assertEqual(config.stt_compute_type, "auto")
            self.assertTrue(config.stt_gpu_fallback_to_cpu)
            self.assertEqual(config.stt_device_index, 1)
            self.assertTrue(config.stt_warmup_on_boot)

    def test_provider_auto_selects_cuda_when_diagnostics_detect_gpu(self):
        with patch("jarvis.providers.stt.faster_whisper_provider.stt_gpu_diagnostics", return_value={"cuda_detected": True}):
            provider = FasterWhisperSTTProvider(device="auto", compute_type="auto")
            self.assertEqual(provider.requested_device, "auto")
            self.assertEqual(provider.device, "cuda")
            self.assertEqual(provider.compute_type, "float16")

    def test_provider_auto_selects_cpu_without_gpu(self):
        with patch("jarvis.providers.stt.faster_whisper_provider.stt_gpu_diagnostics", return_value={"cuda_detected": False}):
            provider = FasterWhisperSTTProvider(device="auto", compute_type="auto")
            self.assertEqual(provider.device, "cpu")
            self.assertEqual(provider.compute_type, "int8")

    def test_compute_type_aliases(self):
        self.assertEqual(_resolve_compute_type("fp16", "cuda"), "float16")
        self.assertEqual(_resolve_compute_type("int8-float16", "cuda"), "int8_float16")
        self.assertEqual(_resolve_compute_type("auto", "cpu"), "int8")

    def test_manager_gpu_status_formats_without_real_gpu(self):
        config = type("Cfg", (), {
            "project_root": Path.cwd(),
            "stt_enabled": True,
            "stt_provider": "mock",
            "stt_fallback_providers": "",
            "stt_mock_text": "hello",
            "stt_output_dir": "data/stt",
            "stt_language": "en",
            "stt_record_seconds": 1.0,
            "stt_sample_rate": 16000,
            "stt_channels": 1,
            "stt_microphone_device": "",
            "stt_device": "auto",
            "stt_compute_type": "auto",
        })()
        manager = STTManager(config)
        output = manager.gpu_status()
        self.assertIn("STT GPU diagnostics", output)
        self.assertIn("requested device: auto", output)


if __name__ == "__main__":
    unittest.main()
