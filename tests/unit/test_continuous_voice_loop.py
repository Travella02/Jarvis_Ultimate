import unittest

from jarvis.clients.cli.cli_client import _parse_voice_loop_continuous_command
from jarvis.core.config import JarvisConfig
from jarvis.core.lifecycle import JarvisRuntime


class TestContinuousVoiceLoopConfigAndCLI(unittest.TestCase):
    def test_parse_handsfree_start_defaults_to_wake_required(self):
        self.assertEqual(
            _parse_voice_loop_continuous_command("handsfree start max 5 silence 0.7"),
            {"max_turns": 5, "require_wake_word": True, "mode": None, "duration_seconds": None, "silence_seconds": 0.7},
        )

    def test_parse_conversation_start_defaults_to_no_wake(self):
        self.assertEqual(
            _parse_voice_loop_continuous_command("conversation start max 3"),
            {"max_turns": 3, "require_wake_word": False, "mode": None, "duration_seconds": None, "silence_seconds": None},
        )

    def test_parse_can_force_no_wake_for_voice_loop(self):
        self.assertEqual(
            _parse_voice_loop_continuous_command("voice loop continuous max 4 no wake"),
            {"max_turns": 4, "require_wake_word": False, "mode": None, "duration_seconds": None, "silence_seconds": None},
        )

    def test_stop_phrase_matching(self):
        phrases = ["stop listening", "go to sleep"]
        self.assertTrue(JarvisRuntime._voice_loop_is_stop_phrase("Stop listening", phrases))
        self.assertTrue(JarvisRuntime._voice_loop_is_stop_phrase("go to sleep please", phrases))
        self.assertFalse(JarvisRuntime._voice_loop_is_stop_phrase("please keep listening", phrases))

    def test_config_reads_continuous_voice_env(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text(
                "JARVIS_VOICE_CONTINUOUS_MAX_TURNS=7\n"
                "JARVIS_VOICE_CONTINUOUS_REQUIRE_WAKE_WORD=false\n"
                "JARVIS_VOICE_CONTINUOUS_STOP_PHRASES=stop now,go offline\n",
                encoding="utf-8",
            )
            config = JarvisConfig.from_project_root(root)
            self.assertEqual(config.voice_continuous_max_turns, 7)
            self.assertFalse(config.voice_continuous_require_wake_word)
            self.assertEqual(config.voice_continuous_stop_phrases, "stop now,go offline")


if __name__ == "__main__":
    unittest.main()
