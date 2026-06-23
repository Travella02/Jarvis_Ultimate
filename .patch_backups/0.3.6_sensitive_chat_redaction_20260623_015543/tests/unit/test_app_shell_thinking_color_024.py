from __future__ import annotations

from pathlib import Path
import re
import unittest


class TestAppShellThinkingColor024(unittest.TestCase):
    def test_renderer_has_purple_thinking_color_and_faster_blend(self) -> None:
        root = Path(__file__).resolve().parents[2]
        renderer = (root / "app_shell" / "renderer" / "renderer.js").read_text(encoding="utf-8")
        self.assertIn("thinking: { r: 168, g: 85, b: 247 }", renderer)
        self.assertIn("colorDt * 1.55", renderer)

    def test_styles_reinforce_purple_thinking_state(self) -> None:
        root = Path(__file__).resolve().parents[2]
        styles = (root / "app_shell" / "renderer" / "styles.css").read_text(encoding="utf-8")
        self.assertRegex(styles, re.compile(r"body\.state-thinking\s*\{[^}]*--state-r:\s*176;", re.S))
        self.assertIn("rgba(176, 76, 255", styles)


if __name__ == "__main__":
    unittest.main()
