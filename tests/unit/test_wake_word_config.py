import tempfile
import unittest
from pathlib import Path

from jarvis.core.config import JarvisConfig


class TestWakeWordConfig(unittest.TestCase):
    def test_reads_wake_settings_from_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".env").write_text(
                "\n".join(
                    [
                        "JARVIS_WAKE_WORD_ENABLED=true",
                        "JARVIS_WAKE_WORD_PROVIDER=phrase",
                        "JARVIS_WAKE_WORDS=computer,hey jarvis",
                        "JARVIS_WAKE_REQUIRE_WAKE_WORD=false",
                        "JARVIS_WAKE_STRIP_WAKE_WORD=false",
                        "JARVIS_WAKE_EMPTY_RESPONSE=At your service, sir.",
                    ]
                ),
                encoding="utf-8",
            )
            config = JarvisConfig.from_project_root(root)
            self.assertTrue(config.wake_word_enabled)
            self.assertEqual(config.wake_word_provider, "phrase")
            self.assertEqual(config.wake_words, "computer,hey jarvis")
            self.assertFalse(config.wake_require_wake_word)
            self.assertFalse(config.wake_strip_wake_word)
            self.assertEqual(config.wake_empty_response, "At your service, sir.")

    def test_reads_wake_settings_from_providers_yaml(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config" / "providers.yaml").write_text(
                """
providers:
  wake_word:
    default: phrase
    enabled: true
    wake_words: hey jarvis,computer
    require_wake_word: true
    strip_wake_word: true
    empty_response: Yes, sir?
""".strip(),
                encoding="utf-8",
            )
            config = JarvisConfig.from_project_root(root)
            self.assertEqual(config.wake_word_provider, "phrase")
            self.assertEqual(config.wake_words, "hey jarvis,computer")
            self.assertTrue(config.wake_require_wake_word)
            self.assertEqual(config.wake_empty_response, "Yes, sir?")


if __name__ == "__main__":
    unittest.main()
