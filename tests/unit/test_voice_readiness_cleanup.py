import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.clients.cli.cli_client import _parse_listen_preset_command, _parse_stt_adaptive_energy_command, _parse_stt_energy_set_command, _parse_stt_silence_set_command
from jarvis.core.config import JarvisConfig
from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.stt.manager import STTManager
from jarvis.providers.tts.manager import TTSManager
from jarvis.providers.stt.base import STTResult
from jarvis.providers.tts.base import TTSResult


class FakeWarmSTT:
    enabled = True
    provider_name = "fake_stt"
    listen_mode = "smart"
    silence_seconds = 0.75
    record_seconds = 2.0
    max_audio_files = 30

    def __init__(self):
        self.warmed = 0
        self.cleaned = 0

    def warmup(self):
        self.warmed += 1
        return STTResult.ok("fake STT warmed", provider="fake_stt", text="")

    def cleanup_recordings(self):
        self.cleaned += 1
        return 2

    def status(self):
        return "fake STT status"


class FakeWarmTTS:
    enabled = True
    provider_name = "fake_tts"
    auto_speak = False
    playback = False
    max_output_files = 30

    def __init__(self):
        self.warmed = 0
        self.cleaned = 0

    def warmup(self):
        self.warmed += 1
        return TTSResult.ok("fake TTS warmed", provider="fake_tts")

    def cleanup_outputs(self):
        self.cleaned += 1
        return 3

    def status(self):
        return "fake TTS status"


class TestVoiceReadinessCleanup(unittest.TestCase):
    def test_config_reads_retention_and_warmup_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text(
                "JARVIS_TTS_MAX_OUTPUT_FILES=11\n"
                "JARVIS_STT_MAX_AUDIO_FILES=12\n"
                "JARVIS_VOICE_WARMUP_ON_BOOT=true\n"
                "JARVIS_VOICE_WARMUP_STT=false\n"
                "JARVIS_VOICE_WARMUP_TTS=true\n",
                encoding="utf-8",
            )
            config = JarvisConfig.from_project_root(root)
            self.assertEqual(config.tts_max_output_files, 11)
            self.assertEqual(config.stt_max_audio_files, 12)
            self.assertTrue(config.voice_warmup_on_boot)
            self.assertFalse(config.voice_warmup_stt)
            self.assertTrue(config.voice_warmup_tts)

    def test_tts_cleanup_keeps_newest_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "data" / "tts"
            output_dir.mkdir(parents=True)
            for index in range(5):
                path = output_dir / f"jarvis_tts_test_{index}.wav"
                path.write_bytes(b"wav")
                os.utime(path, (time.time() + index, time.time() + index))
            config = SimpleNamespace(
                project_root=root,
                tts_enabled=True,
                tts_auto_speak=False,
                tts_provider="mock",
                tts_fallback_providers="",
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
                tts_max_output_files=2,
                tts_delete_after_playback=False,
            )
            manager = TTSManager(config)
            removed = manager.cleanup_outputs()
            self.assertEqual(removed, 3)
            self.assertEqual(len(list(output_dir.glob("jarvis_tts_*.wav"))), 2)

    def test_stt_cleanup_keeps_newest_recordings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output_dir = root / "data" / "stt"
            output_dir.mkdir(parents=True)
            for index in range(4):
                path = output_dir / f"jarvis_mic_test_{index}.wav"
                path.write_bytes(b"wav")
                os.utime(path, (time.time() + index, time.time() + index))
            config = SimpleNamespace(
                project_root=root,
                stt_enabled=True,
                stt_provider="mock",
                stt_fallback_providers="",
                stt_mock_text="hello sir",
                stt_output_dir="data/stt",
                stt_language="en",
                stt_record_seconds=2.0,
                stt_listen_mode="smart",
                stt_max_listen_seconds=8.0,
                stt_silence_seconds=0.75,
                stt_min_record_seconds=0.25,
                stt_start_timeout_seconds=4.0,
                stt_energy_threshold=0.012,
                stt_pre_roll_seconds=0.25,
                stt_frame_ms=30,
                stt_sample_rate=16000,
                stt_channels=1,
                stt_microphone_device="",
                stt_max_audio_files=1,
            )
            manager = STTManager(config)
            removed = manager.cleanup_recordings()
            self.assertEqual(removed, 3)
            self.assertEqual(len(list(output_dir.glob("jarvis_mic_*.wav"))), 1)

    def test_energy_and_adaptive_parsers(self):
        self.assertEqual(_parse_stt_energy_set_command("stt energy 0.03"), 0.03)
        self.assertEqual(_parse_stt_energy_set_command("energy threshold 0.025"), 0.025)
        self.assertIsNone(_parse_stt_energy_set_command("stt energy auto"))
        self.assertTrue(_parse_stt_adaptive_energy_command("stt adaptive on"))
        self.assertFalse(_parse_stt_adaptive_energy_command("stt adaptive off"))
        self.assertIsNone(_parse_stt_adaptive_energy_command("adaptive maybe"))

    def test_runtime_warmup_and_audio_cleanup_helpers(self):
        with tempfile.TemporaryDirectory() as tmp:
            stt = FakeWarmSTT()
            tts = FakeWarmTTS()
            runtime = JarvisRuntime(project_root=tmp, stt_manager=stt, tts_manager=tts)
            text = runtime.warmup_all()
            self.assertIn("fake STT warmed", text)
            self.assertIn("fake TTS warmed", text)
            self.assertEqual(stt.warmed, 1)
            self.assertEqual(tts.warmed, 1)
            cleanup = runtime.audio_cleanup()
            self.assertIn("Removed 3 TTS", cleanup)
            self.assertIn("2 STT", cleanup)

    def test_listen_preset_and_silence_parsers(self):
        self.assertEqual(_parse_listen_preset_command("listen faster"), "faster")
        self.assertEqual(_parse_listen_preset_command("listen safer"), "safer")
        self.assertIsNone(_parse_listen_preset_command("listen to music"))
        self.assertEqual(_parse_stt_silence_set_command("stt silence 0.7"), 0.7)
        self.assertEqual(_parse_stt_silence_set_command("set silence 1.1 seconds"), 1.1)
        self.assertIsNone(_parse_stt_silence_set_command("set silence potato"))


if __name__ == "__main__":
    unittest.main()
