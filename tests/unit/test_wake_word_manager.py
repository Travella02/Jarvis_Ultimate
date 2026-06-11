import tempfile
import unittest

from jarvis.core.config import JarvisConfig
from jarvis.providers.wake_word.manager import WakeWordManager


class TestWakeWordManager(unittest.TestCase):
    def test_detects_wake_word_and_extracts_command(self):
        manager = WakeWordManager(JarvisConfig(project_root=tempfile.gettempdir()))
        match = manager.detect("Hey Jarvis, give me one sentence")
        self.assertTrue(match.detected)
        self.assertEqual(match.wake_word, "hey jarvis")
        self.assertEqual(match.command, "give me one sentence")

    def test_detects_empty_wake_phrase(self):
        manager = WakeWordManager(JarvisConfig(project_root=tempfile.gettempdir()))
        match = manager.detect("Hey Jarvis")
        self.assertTrue(match.detected)
        self.assertEqual(match.command, "")
        self.assertIn("no command", match.message.lower())

    def test_rejects_non_wake_transcript(self):
        manager = WakeWordManager(JarvisConfig(project_root=tempfile.gettempdir()))
        match = manager.detect("This is just a normal sentence")
        self.assertFalse(match.detected)
        self.assertEqual(match.command, "")

    def test_status_reports_configured_wake_words(self):
        config = JarvisConfig(project_root=tempfile.gettempdir(), wake_words="computer,hey jarvis")
        manager = WakeWordManager(config)
        status = manager.status()
        self.assertIn("computer", status)
        self.assertIn("hey jarvis", status)


if __name__ == "__main__":
    unittest.main()
