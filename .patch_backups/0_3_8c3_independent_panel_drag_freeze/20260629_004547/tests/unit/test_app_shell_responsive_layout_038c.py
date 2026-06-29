import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class AppShellResponsiveLayout038cTests(unittest.TestCase):
    def test_version_and_capabilities_include_responsive_resize_guards(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.8c2")
        capabilities = set(app_shell_capabilities())
        self.assertIn("responsive_panel_resize_clamping", capabilities)
        self.assertIn("floating_panel_viewport_bounds", capabilities)
        self.assertIn("debounced_layout_resize_handler", capabilities)

    def test_renderer_clamps_floating_panel_layouts_to_viewport(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("PANEL_VIEWPORT_MARGIN", renderer)
        self.assertIn("PANEL_MIN_FLOATING_WIDTH", renderer)
        self.assertIn("viewportPanelBounds", renderer)
        self.assertIn("clampPanelLayoutToViewport", renderer)
        self.assertIn("scheduleResponsiveLayoutClamp", renderer)
        self.assertIn("window.addEventListener('resize', scheduleResponsiveLayoutClamp)", renderer)
        self.assertIn("document.querySelector('.dockable-panel.is-dragging, .dockable-panel.is-resizing')", renderer)

    def test_styles_keep_floating_panels_bounded_during_window_resize(self):
        css = Path("app_shell/renderer/styles.css").read_text(encoding="utf-8")
        self.assertIn("responsive window resize guard", css)
        self.assertIn("max-width: calc(100vw - 16px)", css)
        self.assertIn("max-height: calc(100vh - 16px)", css)
        self.assertIn("grid-template-columns: minmax(0, 1fr)", css)
        self.assertNotIn("position: relative !important; left: auto !important; top: auto", css)


if __name__ == "__main__":
    unittest.main()
