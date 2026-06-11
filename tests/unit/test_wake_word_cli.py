import unittest

from jarvis.clients.cli.cli_client import (
    _parse_wake_listen_command,
    _parse_wake_test_command,
    _parse_wake_voice_command,
)


class TestWakeWordCLI(unittest.TestCase):
    def test_parse_wake_test_preserves_text(self):
        self.assertEqual(_parse_wake_test_command("wake test Hey Jarvis, status"), "Hey Jarvis, status")

    def test_parse_wake_listen_once(self):
        self.assertEqual(_parse_wake_listen_command("wake listen once"), {"mode": None, "duration_seconds": None, "silence_seconds": None})

    def test_parse_wake_voice_tuning(self):
        self.assertEqual(
            _parse_wake_voice_command("wake loop smart max 8 silence 0.8"),
            {"mode": "smart", "duration_seconds": 8.0, "silence_seconds": 0.8},
        )

    def test_rejects_unrelated_text(self):
        self.assertIsNone(_parse_wake_voice_command("wake me up tomorrow"))


if __name__ == "__main__":
    unittest.main()
