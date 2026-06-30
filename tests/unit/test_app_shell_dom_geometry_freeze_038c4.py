import unittest
from pathlib import Path

from jarvis.clients.app_shell.bridge import APP_SHELL_VERSION, app_shell_capabilities


class AppShellDomGeometryFreeze038c4Tests(unittest.TestCase):
    def test_version_and_capabilities_include_release_snap_guard(self):
        self.assertEqual(APP_SHELL_VERSION, "0.3.8d4")
        capabilities = set(app_shell_capabilities())
        self.assertIn("dom_geometry_panel_freeze", capabilities)
        self.assertIn("post_drag_neighbor_snap_guard", capabilities)
        self.assertIn("release_safe_panel_layout_restore", capabilities)

    def test_renderer_captures_real_panel_geometry_before_drag(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("layoutRecordFromPanelGeometry", renderer)
        self.assertIn("panel?.getBoundingClientRect?.()", renderer)
        self.assertIn("capturePanelInteractionLayout(activeKey)", renderer)
        self.assertIn("layoutRecordFromPanelGeometry(panel, { forceFloating: true })", renderer)
        self.assertIn("applyFrozenPanelSnapshot(activePanelInteractionSnapshot, key)", renderer)
        self.assertIn("freeze each unaffected panel from its real DOM geometry", renderer)

    def test_preserved_floating_records_are_sanitized_without_reintroducing_stale_geometry(self):
        renderer = Path("app_shell/renderer/renderer.js").read_text(encoding="utf-8")
        self.assertIn("const preservedKeys = new Set(options.preserveKeys || [])", renderer)
        self.assertIn("? sanitizeLayoutRecord({ ...existing, mode: 'floating' }, key)", renderer)
        self.assertNotIn("...sanitizeLayoutRecord({ ...existing, mode: 'floating' }, key), ...existing", renderer)


if __name__ == "__main__":
    unittest.main()
