import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class TestAppShellInterfaceControls019a(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[2]
        self.index_html = (self.root / "app_shell" / "renderer" / "index.html").read_text(encoding="utf-8")
        self.styles_css = (self.root / "app_shell" / "renderer" / "styles.css").read_text(encoding="utf-8")
        self.renderer_js = (self.root / "app_shell" / "renderer" / "renderer.js").read_text(encoding="utf-8")

    def test_version_and_capabilities_include_019a_controls(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.1c")
        capabilities = app_shell_capabilities()
        self.assertIn("panel_visibility_controls", capabilities)
        self.assertIn("orb_only_focus_mode", capabilities)
        self.assertIn("auto_sleep_wake_startup", capabilities)
        self.assertIn("state_color_palette_refinement", capabilities)
        self.assertIn("dim_sleep_mode_motion", capabilities)

    def test_index_exposes_panel_toggles_and_auto_wake(self):
        self.assertIn('data-panel-toggle="runtime"', self.index_html)
        self.assertIn('data-panel-toggle="voice"', self.index_html)
        self.assertIn('data-panel-toggle="workspace"', self.index_html)
        self.assertIn('data-panel-toggle="conversation"', self.index_html)
        self.assertIn('data-panel-toggle="diagnostics"', self.index_html)
        self.assertIn('id="orbFocusButton"', self.index_html)
        self.assertIn('id="autoWakeToggle"', self.index_html)

    def test_renderer_persists_panel_visibility_and_auto_starts_sleep_wake(self):
        self.assertIn("PANEL_STORAGE_KEY", self.renderer_js)
        self.assertIn("togglePanel", self.renderer_js)
        self.assertIn("toggleOrbFocus", self.renderer_js)
        self.assertIn("maybeAutoStartSleepWake", self.renderer_js)
        self.assertIn("startSleepWake({ automatic: true })", self.renderer_js)

    def test_styles_define_state_palette_and_hidden_panels(self):
        self.assertIn("body.state-sleeping", self.styles_css)
        self.assertIn("--orb-opacity: .52", self.styles_css)
        self.assertIn("body.state-thinking", self.styles_css)
        self.assertIn("--state-r: 168", self.styles_css)
        self.assertIn("body.state-speaking", self.styles_css)
        self.assertIn("--state-r: 31", self.styles_css)
        self.assertIn("panel-runtime-hidden", self.styles_css)
        self.assertIn("body.orb-focus", self.styles_css)
        self.assertIn("left-rail-empty", self.styles_css)


if __name__ == "__main__":
    unittest.main()
