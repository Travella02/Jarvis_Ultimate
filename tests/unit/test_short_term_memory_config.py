from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from jarvis.core.config import JarvisConfig


class TestShortTermMemoryConfig(unittest.TestCase):
    def test_env_file_short_term_memory_settings_are_loaded(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text(
                "\n".join(
                    [
                        "JARVIS_MEMORY_SHORT_TERM_ENABLED=false",
                        "JARVIS_MEMORY_SHORT_TERM_MAX_TURNS=7",
                        "JARVIS_MEMORY_SHORT_TERM_MAX_CHARS=3456",
                        "JARVIS_MEMORY_SHORT_TERM_INJECT_LAST_TURNS=3",
                        "JARVIS_MEMORY_SHORT_TERM_AUTOSAVE=true",
                    ]
                ),
                encoding="utf-8",
            )

            config = JarvisConfig.from_project_root(root)

            self.assertFalse(config.memory_short_term_enabled)
            self.assertEqual(config.memory_short_term_max_turns, 7)
            self.assertEqual(config.memory_short_term_max_chars, 3456)
            self.assertEqual(config.memory_short_term_inject_last_turns, 3)
            self.assertTrue(config.memory_short_term_autosave)


if __name__ == "__main__":
    unittest.main()
