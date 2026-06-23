from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import unittest

from jarvis.ui.themes import available_themes, get_theme, state_color, status_color, validate_theme


class TestUIThemeSystem(unittest.TestCase):
    def test_builtin_themes_are_available(self):
        names = available_themes()
        self.assertIn("jarvis_dark", names)
        self.assertIn("cyber_blue", names)
        self.assertIn("stealth_black", names)

    def test_get_theme_returns_copy_with_required_tokens(self):
        theme = get_theme("cyber_blue")
        validate_theme(theme)
        theme["accent"] = "changed"
        self.assertNotEqual(get_theme("cyber_blue")["accent"], "changed")

    def test_unknown_theme_falls_back_safely(self):
        self.assertEqual(get_theme("does_not_exist")["name"], "Jarvis Dark")

    def test_state_and_status_colors_resolve(self):
        theme = get_theme()
        self.assertEqual(state_color("speaking", theme), "#34d399")
        self.assertEqual(status_color("running", theme), theme["success"])
        self.assertEqual(status_color("totally unknown", theme), theme["muted"])


if __name__ == "__main__":
    unittest.main()
