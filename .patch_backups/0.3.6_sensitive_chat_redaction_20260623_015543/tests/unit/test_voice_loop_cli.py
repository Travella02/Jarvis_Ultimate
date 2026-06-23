import unittest

from jarvis.clients.cli.cli_client import _parse_voice_loop_command


class TestVoiceLoopCLI(unittest.TestCase):
    def test_parse_simple_voice_loop_commands(self):
        self.assertEqual(_parse_voice_loop_command("voice loop once"), {"mode": None, "duration_seconds": None, "silence_seconds": None})
        self.assertEqual(_parse_voice_loop_command("talk once"), {"mode": None, "duration_seconds": None, "silence_seconds": None})
        self.assertEqual(_parse_voice_loop_command("listen and respond"), {"mode": None, "duration_seconds": None, "silence_seconds": None})

    def test_parse_voice_loop_tuning_commands(self):
        self.assertEqual(_parse_voice_loop_command("voice loop smart max 8 silence 0.8"), {"mode": "smart", "duration_seconds": 8.0, "silence_seconds": 0.8})
        self.assertEqual(_parse_voice_loop_command("voice loop fixed 2"), {"mode": "fixed", "duration_seconds": 2.0, "silence_seconds": None})

    def test_rejects_unrelated_command(self):
        self.assertIsNone(_parse_voice_loop_command("voice memo"))


if __name__ == "__main__":
    unittest.main()
