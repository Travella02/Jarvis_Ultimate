import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class AppShellPanelStability038bTests(unittest.TestCase):
    def test_version_and_capabilities_include_panel_stability_guards(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.8c1")
        capabilities = set(app_shell_capabilities())
        self.assertIn("panel_header_no_overlap_guard", capabilities)
        self.assertIn("panel_drag_placeholder_stabilization", capabilities)

    def test_renderer_uses_placeholder_when_promoting_docked_panel_to_floating(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("createPanelLayoutPlaceholder", renderer)
        self.assertIn("removePanelLayoutPlaceholder", renderer)
        self.assertIn("promotePanelToFloating", renderer)
        self.assertIn("placeholder = wasFloating ? null : createPanelLayoutPlaceholder", renderer)
        self.assertIn("removePanelLayoutPlaceholder(placeholder)", renderer)

    def test_styles_contain_wrapping_panel_actions_and_placeholder(self):
        css = Path("app_shell/renderer/styles.css").read_text(encoding="utf-8")
        self.assertIn("panel header containment", css)
        self.assertIn(".dockable-panel .panel-layout-actions", css)
        self.assertIn("flex-wrap: wrap", css)
        self.assertIn(".panel-layout-placeholder", css)
        self.assertIn("visibility: hidden", css)
        self.assertIn(".layout-preset-select option", css)


if __name__ == "__main__":
    unittest.main()
