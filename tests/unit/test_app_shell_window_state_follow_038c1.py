import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class AppShellWindowStateFollow038c1Tests(unittest.TestCase):
    def test_version_and_capabilities_include_window_state_follow_hotfix(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.8d4")
        capabilities = set(app_shell_capabilities())
        self.assertIn("viewport_scaled_panel_restore", capabilities)
        self.assertIn("last_active_panel_z_order", capabilities)
        self.assertIn("floating_panel_content_containment", capabilities)
        self.assertIn("runtime_panel_minimum_size_guard", capabilities)

    def test_renderer_scales_floating_layouts_between_viewport_sizes(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("PANEL_LAYOUT_VIEWPORT_STORAGE_KEY", renderer)
        self.assertIn("currentPanelViewportSnapshot", renderer)
        self.assertIn("savePanelLayoutViewport", renderer)
        self.assertIn("inferPanelLayoutViewport", renderer)
        self.assertIn("scaleFloatingLayoutForViewport", renderer)
        self.assertIn("reconcilePanelLayoutToViewport", renderer)
        self.assertIn("window.addEventListener('orientationchange', scheduleResponsiveLayoutClamp)", renderer)

    def test_renderer_tracks_last_active_panel_z_order(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("PANEL_BASE_Z_INDEX", renderer)
        self.assertIn("initialPanelZIndexCounter", renderer)
        self.assertIn("bringPanelToFront", renderer)
        self.assertIn("panel.style.zIndex", renderer)
        self.assertIn("panel.addEventListener('pointerdown', () => bringPanelToFront", renderer)

    def test_renderer_and_css_guard_runtime_content_minimums(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        css = Path("app_shell/renderer/styles.css").read_text(encoding="utf-8")
        self.assertIn("panelMinimums", renderer)
        self.assertIn("runtime: { width: 330, height: 186 }", renderer)
        self.assertIn("floating_panel_content_containment", Path("src/jarvis/clients/app_shell/bridge.py").read_text(encoding="utf-8"))
        self.assertIn("0.3.8c4: viewport-follow", css)
        self.assertIn(".system-card.layout-floating:not(.panel-minimized)", css)
        self.assertIn("min-width: 330px", css)
        self.assertIn("overflow: auto", css)


if __name__ == "__main__":
    unittest.main()
