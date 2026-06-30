import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class AppShellWorkspaceSafeScaling038c2Tests(unittest.TestCase):
    def test_version_and_capabilities_include_safe_workspace_scaling(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.8d")
        capabilities = set(app_shell_capabilities())
        self.assertIn("workspace_safe_area_panel_scaling", capabilities)
        self.assertIn("maximize_restore_panel_ratio_preservation", capabilities)
        self.assertIn("top_bar_overlap_prevention", capabilities)

    def test_renderer_uses_workspace_bounds_for_floating_panel_scaling(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("PANEL_WORKSPACE_SELECTOR", renderer)
        self.assertIn("#interfaceGrid", renderer)
        self.assertIn("workspace.getBoundingClientRect()", renderer)
        self.assertIn("left: Math.max(0, rect.left)", renderer)
        self.assertIn("top: Math.max(0, rect.top)", renderer)
        self.assertIn("previousOriginY = previous.top + previous.margin", renderer)
        self.assertIn("nextOriginY = next.top + next.margin", renderer)
        self.assertIn("bounds.bottom - height - bounds.margin", renderer)

    def test_css_documents_workspace_safe_area_hotfix(self):
        css = Path("app_shell/renderer/styles.css").read_text(encoding="utf-8")
        self.assertIn("0.3.8c4: floating panels now scale inside the workspace safe area", css)
        self.assertIn(".dockable-panel.layout-floating", css)


if __name__ == "__main__":
    unittest.main()
