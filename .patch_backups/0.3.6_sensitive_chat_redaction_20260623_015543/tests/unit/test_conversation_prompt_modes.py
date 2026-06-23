from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import unittest

from jarvis.agents.conversation_agent.prompts import (
    MINIMAL_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
    get_prompt_stats,
    get_system_prompt,
    normalize_prompt_mode,
)


class TestConversationPromptModes(unittest.TestCase):
    def test_normal_prompt_is_default(self):
        self.assertEqual(normalize_prompt_mode(None), "normal")
        self.assertEqual(get_system_prompt(None), SYSTEM_PROMPT)

    def test_minimal_prompt_aliases_are_supported(self):
        self.assertEqual(normalize_prompt_mode("fast"), "minimal")
        self.assertEqual(normalize_prompt_mode("short"), "minimal")
        self.assertEqual(get_system_prompt("minimal"), MINIMAL_SYSTEM_PROMPT)
        self.assertLess(len(MINIMAL_SYSTEM_PROMPT), len(SYSTEM_PROMPT))

    def test_prompt_can_be_disabled_for_speed_tests(self):
        self.assertEqual(normalize_prompt_mode("none"), "off")
        self.assertIsNone(get_system_prompt("off"))
        stats = get_prompt_stats("off")
        self.assertEqual(stats["mode"], "off")
        self.assertFalse(stats["enabled"])
        self.assertEqual(stats["chars"], 0)


if __name__ == "__main__":
    unittest.main()
