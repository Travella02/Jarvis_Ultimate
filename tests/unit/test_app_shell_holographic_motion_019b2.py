import unittest
from pathlib import Path


class TestAppShellHolographicMotion019b2(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2]
        self.styles_css = (root / "app_shell" / "renderer" / "styles.css").read_text(encoding="utf-8")
        self.renderer_js = (root / "app_shell" / "renderer" / "renderer.js").read_text(encoding="utf-8")

    def test_sleep_mode_keeps_slow_rings_and_breathing(self):
        self.assertIn("body.state-sleeping .orb-ring", self.styles_css)
        self.assertIn("--ring-a-rot", self.styles_css)
        self.assertIn("motionProfileForState", self.renderer_js)
        self.assertIn("ringA: 5.8", self.renderer_js)
        self.assertIn("sleepOrbBreathe 10.8s", self.styles_css)
        self.assertIn("scale(1.038)", self.styles_css)

    def test_speaking_uses_rings_not_waves(self):
        self.assertIn("body.state-speaking .voice-wave { opacity: 0; animation: none; }", self.styles_css)
        self.assertIn("body.state-speaking .ring-a", self.styles_css)
        self.assertIn("body.state-speaking .ring-c", self.styles_css)
        self.assertIn("ringA: 10.8", self.renderer_js)

    def test_ui_is_nearly_black_with_holographic_glass(self):
        self.assertIn("linear-gradient(135deg, #000000 0%, #000000 72%, #000000 100%)", self.styles_css)
        self.assertIn("rgba(35, 171, 255, 0.018)", self.styles_css)
        self.assertIn("edge-only holographic panels", self.styles_css)
        self.assertIn("rgba(0, 4, 11, .075)", self.styles_css)

    def test_state_blend_window_is_longer(self):
        self.assertIn("--state-transition: 3.1s cubic-bezier", self.styles_css)
        self.assertIn("document.body.classList.add('state-fading')", self.renderer_js)
        self.assertIn("3100", self.renderer_js)


if __name__ == "__main__":
    unittest.main()
