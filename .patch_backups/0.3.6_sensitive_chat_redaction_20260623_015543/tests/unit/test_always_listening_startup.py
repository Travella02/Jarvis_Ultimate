import tempfile
import unittest
from pathlib import Path

from jarvis.clients.cli.cli_client import _parse_sleep_wake_command
from jarvis.core.config import JarvisConfig
from jarvis.core.lifecycle import JarvisRuntime
from jarvis.providers.llm.mock_provider import MockLLMProvider
from tests.unit.test_sleep_wake_voice_loop import FakeTTSManager, SequenceSTTManager


class TestAlwaysListeningStartup(unittest.TestCase):
    def test_config_reads_startup_always_listening_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text(
                "JARVIS_VOICE_WARMUP_ON_BOOT=true\n"
                "JARVIS_VOICE_ALWAYS_LISTENING_ON_STARTUP=true\n"
                "JARVIS_VOICE_ALWAYS_LISTENING_MAX_TURNS=0\n"
                "JARVIS_VOICE_ALWAYS_LISTENING_START_MODE=sleep_wake\n",
                encoding="utf-8",
            )
            config = JarvisConfig.from_project_root(root)
            self.assertTrue(config.voice_warmup_on_boot)
            self.assertTrue(config.voice_always_listening_on_startup)
            self.assertEqual(config.voice_always_listening_max_turns, 0)
            self.assertEqual(config.voice_always_listening_start_mode, "sleep_wake")

    def test_parse_sleep_wake_forever(self):
        self.assertEqual(
            _parse_sleep_wake_command("sleep wake start forever timeout 30 silence 0.65"),
            {"max_turns": 0, "active_timeout_seconds": 30.0, "mode": None, "duration_seconds": None, "silence_seconds": 0.65},
        )
        self.assertEqual(
            _parse_sleep_wake_command("always listening start max 0 timeout 45"),
            {"max_turns": 0, "active_timeout_seconds": 45.0, "mode": None, "duration_seconds": None, "silence_seconds": None},
        )

    def test_sleep_wake_loop_allows_infinite_until_exit_phrase(self):
        with tempfile.TemporaryDirectory() as tmp:
            stt = SequenceSTTManager([
                "Hey Jarvis, give me one sentence",
                "exit voice mode",
            ])
            runtime = JarvisRuntime(
                project_root=tmp,
                llm_provider=MockLLMProvider(canned_response="Standing by, sir."),
                stt_manager=stt,
                tts_manager=FakeTTSManager(),
            )
            runtime.boot()
            status = []
            result = runtime.voice_sleep_wake_loop(max_turns=0, active_timeout_seconds=45, status_callback=status.append, speak=False)
            self.assertTrue(result.success)
            self.assertEqual(result.data["stopped_by"], "spoken_exit_phrase")
            self.assertTrue(result.data["infinite"])
            self.assertEqual(result.data["wake_activations"], 1)
            self.assertTrue(any("Listening turn 1/∞" in item for item in status))
            runtime.spoken_pipeline.shutdown()

    def test_startup_status_uses_infinite_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text(
                "JARVIS_VOICE_ALWAYS_LISTENING_ON_STARTUP=true\n"
                "JARVIS_VOICE_ALWAYS_LISTENING_MAX_TURNS=0\n",
                encoding="utf-8",
            )
            runtime = JarvisRuntime(project_root=root, llm_provider=MockLLMProvider(), stt_manager=SequenceSTTManager([]), tts_manager=FakeTTSManager())
            runtime.boot()
            status = runtime.startup_always_listening_status()
            self.assertIn("enabled: True", status)
            self.assertIn("max turns: infinite", status)
            runtime.spoken_pipeline.shutdown()


if __name__ == "__main__":
    unittest.main()
