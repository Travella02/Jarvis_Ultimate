import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class TestAppShellHolographicSleep019b(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.styles_css = (self.root / "app_shell" / "renderer" / "styles.css").read_text(encoding="utf-8")
        self.renderer_js = (self.root / "app_shell" / "renderer" / "renderer.js").read_text(encoding="utf-8")

    def test_version_and_capabilities_include_019b_refinements(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.1")
        capabilities = app_shell_capabilities()
        self.assertIn("constant_grey_sleep_mode", capabilities)
        self.assertIn("holographic_transparent_panels", capabilities)
        self.assertIn("blended_state_color_transitions", capabilities)
        self.assertIn("voice_panel_overflow_fix", capabilities)

    def test_styles_use_animatable_state_channels_for_blended_color_changes(self):
        self.assertIn("@property --state-r", self.styles_css)
        self.assertIn("--state-transition: 3.1s", self.styles_css)
        self.assertIn("--state-r var(--state-transition)", self.styles_css)
        self.assertIn("--state-g var(--state-transition)", self.styles_css)
        self.assertIn("--state-b var(--state-transition)", self.styles_css)
        self.assertIn("body.state-fading", self.styles_css)

    def test_sleep_mode_uses_constant_grey_orb_and_slow_motion(self):
        self.assertIn("constant dim grey", self.styles_css)
        self.assertIn("sleepOrbBreathe", self.styles_css)
        self.assertIn("#7b858c", self.styles_css)
        self.assertIn("filter: grayscale(1)", self.styles_css)
        self.assertIn("body.state-sleeping .orb-ring", self.styles_css)
        self.assertIn("--ring-a-rot", self.styles_css)

    def test_voice_panel_prevents_button_and_chip_overflow(self):
        self.assertIn("overflow-x: hidden", self.styles_css)
        self.assertIn(".voice-card .panel-heading", self.styles_css)
        self.assertIn(".voice-card .voice-chip", self.styles_css)
        self.assertIn("text-overflow: ellipsis", self.styles_css)

    def test_holographic_background_and_panels_are_darker_and_more_transparent(self):
        self.assertIn("#000000", self.styles_css)
        self.assertIn("rgba(0, 3, 8, 0.035)", self.styles_css)
        self.assertIn("backdrop-filter: blur(22px)", self.styles_css)
        self.assertIn("holographic", self.styles_css.lower())

    def test_renderer_tracks_state_fade_transitions(self):
        self.assertIn("stateFadeTimer", self.renderer_js)
        self.assertIn("state-fading", self.renderer_js)
        self.assertIn("activeVisualState", self.renderer_js)
        self.assertIn("v021", self.renderer_js)
        self.assertIn("3100", self.renderer_js)


if __name__ == "__main__":
    unittest.main()
