import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class AppShellIndependentPanelDrag038c3Tests(unittest.TestCase):
    def test_version_and_capabilities_include_independent_panel_drag_freeze(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.8d4")
        capabilities = set(app_shell_capabilities())
        self.assertIn("independent_panel_drag_freeze", capabilities)
        self.assertIn("active_panel_only_drag_updates", capabilities)
        self.assertIn("no_neighbor_panel_reflow_on_drag", capabilities)

    def test_renderer_freezes_unaffected_panels_during_drag_and_resize(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("PANEL_LAYOUT_INTERACTION_SETTLE_MS", renderer)
        self.assertIn("capturePanelInteractionLayout", renderer)
        self.assertIn("startPanelLayoutInteraction", renderer)
        self.assertIn("finishPanelLayoutInteraction", renderer)
        self.assertIn("restoreUnaffectedPanelLayout", renderer)
        self.assertIn("isPanelLayoutInteractionActive", renderer)
        self.assertIn("applyPanelLayout({ preserveKeys: Object.keys(interactionSnapshot || {}) })", renderer)
        self.assertIn("active panel interactions freeze every other panel", renderer)

    def test_render_state_and_responsive_clamp_do_not_reflow_during_panel_interaction(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("if (!isPanelLayoutInteractionActive())", renderer)
        self.assertIn("document.querySelector('.dockable-panel.is-dragging, .dockable-panel.is-resizing') || isPanelLayoutInteractionActive()", renderer)
        self.assertIn("const preservedKeys = new Set(options.preserveKeys || [])", renderer)


if __name__ == "__main__":
    unittest.main()
